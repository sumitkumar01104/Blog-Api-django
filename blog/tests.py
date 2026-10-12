from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Post, Comment, Like

STRONG_PW = 'Xk9#mPq2vL'


def make_user(name, **kw):
    return User.objects.create_user(name, password=STRONG_PW, **kw)


# ---------------------------------------------------------------- MODELS
class ModelTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.post = Post.objects.create(title='Hello', content='World', author=self.user)

    def test_post_str(self):
        self.assertEqual(str(self.post), 'Hello')

    def test_comment_str(self):
        c = Comment.objects.create(post=self.post, author=self.user, content='nice')
        self.assertEqual(str(c), 'sumit → Hello')

    def test_like_str(self):
        l = Like.objects.create(post=self.post, user=self.user)
        self.assertEqual(str(l), 'sumit liked Hello')

    def test_like_unique_together(self):
        from django.db import IntegrityError, transaction
        Like.objects.create(post=self.post, user=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Like.objects.create(post=self.post, user=self.user)

    def test_deleting_post_deletes_comments_and_likes(self):
        Comment.objects.create(post=self.post, author=self.user, content='c')
        Like.objects.create(post=self.post, user=self.user)
        self.post.delete()
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(Like.objects.count(), 0)

    def test_deleting_user_deletes_posts(self):
        self.user.delete()
        self.assertEqual(Post.objects.count(), 0)


# ---------------------------------------------------------------- FRONTEND
class FrontendTests(APITestCase):
    def test_home_page_renders(self):
        res = self.client.get(reverse('blog'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'blog-frontend.html')


# ---------------------------------------------------------------- REGISTER
class RegisterTests(APITestCase):
    url = '/register/'

    def test_register_success(self):
        res = self.client.post(self.url, {'username': 'sumit', 'password': STRONG_PW}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(username='sumit').exists())

    def test_register_password_is_hashed(self):
        self.client.post(self.url, {'username': 'sumit', 'password': STRONG_PW}, format='json')
        u = User.objects.get(username='sumit')
        self.assertNotEqual(u.password, STRONG_PW)
        self.assertTrue(u.check_password(STRONG_PW))

    def test_register_missing_fields(self):
        for data in ({}, {'username': 'a'}, {'password': STRONG_PW}):
            res = self.client.post(self.url, data, format='json')
            self.assertEqual(res.status_code, 400, data)

    def test_register_duplicate_username(self):
        make_user('sumit')
        res = self.client.post(self.url, {'username': 'sumit', 'password': STRONG_PW}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(User.objects.filter(username='sumit').count(), 1)

    def test_register_password_similar_to_username(self):
        res = self.client.post(self.url, {'username': 'sumit', 'password': 'sumit123'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(username='sumit').exists())

    def test_register_weak_passwords(self):
        for pw in ('short1', '12345678', 'password'):
            res = self.client.post(self.url, {'username': 'u' + pw, 'password': pw}, format='json')
            self.assertEqual(res.status_code, 400, pw)

    def test_register_then_login_gets_token(self):
        self.client.post(self.url, {'username': 'sumit', 'password': STRONG_PW}, format='json')
        res = self.client.post('/api/token/', {'username': 'sumit', 'password': STRONG_PW}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)


# ---------------------------------------------------------------- AUTH / JWT
class AuthTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')

    def test_login_wrong_password(self):
        res = self.client.post('/api/token/', {'username': 'sumit', 'password': 'wrong'}, format='json')
        self.assertEqual(res.status_code, 401)

    def test_access_token_works_on_protected_endpoint(self):
        tokens = self.client.post('/api/token/', {'username': 'sumit', 'password': STRONG_PW}, format='json').data
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        res = self.client.post('/blog/', {'title': 't', 'content': 'c'}, format='json')
        self.assertEqual(res.status_code, 201)

    def test_invalid_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer garbage')
        res = self.client.post('/blog/', {'title': 't', 'content': 'c'}, format='json')
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_gives_new_access(self):
        refresh = str(RefreshToken.for_user(self.user))
        res = self.client.post('/api/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')

    def test_logout_blacklists_refresh_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        res = self.client.post('/logout/', {'refresh': refresh}, format='json')
        self.assertEqual(res.status_code, 200)
        # blacklisted token se naya access nahi milna chahiye
        res = self.client.post('/api/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(res.status_code, 401)

    def test_logout_invalid_token(self):
        res = self.client.post('/logout/', {'refresh': 'junk'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_logout_missing_token(self):
        res = self.client.post('/logout/', {}, format='json')
        self.assertEqual(res.status_code, 400)


# ---------------------------------------------------------------- POSTS
class PostListCreateTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.post = Post.objects.create(title='Hello', content='World', author=self.user)

    def test_list_is_public(self):
        res = self.client.get('/blog/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['title'], 'Hello')

    def test_list_newest_first(self):
        Post.objects.create(title='Newer', content='x', author=self.user)
        titles = [p['title'] for p in self.client.get('/blog/').data['results']]
        self.assertEqual(titles, ['Newer', 'Hello'])

    def test_list_is_paginated_10_per_page(self):
        for i in range(14):
            Post.objects.create(title=f'p{i}', content='x', author=self.user)
        res = self.client.get('/blog/')
        self.assertEqual(res.data['count'], 15)
        self.assertEqual(len(res.data['results']), 10)
        self.assertIsNotNone(res.data['next'])
        res2 = self.client.get('/blog/?page=2')
        self.assertEqual(len(res2.data['results']), 5)

    def test_list_includes_comments_and_like_count(self):
        other = make_user('rahul')
        Comment.objects.create(post=self.post, author=other, content='nice')
        Like.objects.create(post=self.post, user=other)
        item = self.client.get('/blog/').data['results'][0]
        self.assertEqual(item['total_likes'], 1)
        self.assertEqual(item['comments'][0]['content'], 'nice')
        self.assertEqual(item['comments'][0]['author'], 'rahul')
        self.assertEqual(item['author'], 'sumit')

    def test_list_query_count_is_constant(self):
        other = make_user('rahul')
        for i in range(5):
            p = Post.objects.create(title=f'p{i}', content='x', author=self.user)
            Comment.objects.create(post=p, author=other, content='c')
            Like.objects.create(post=p, user=other)
        # N+1 nahi hona chahiye
        with self.assertNumQueries(5):
            self.client.get('/blog/')

    def test_create_requires_login(self):
        res = self.client.post('/blog/', {'title': 'x', 'content': 'y'}, format='json')
        self.assertEqual(res.status_code, 401)

    def test_create_sets_author_from_token(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/blog/', {'title': 'New', 'content': 'Body'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Post.objects.get(title='New').author, self.user)

    def test_create_ignores_author_in_payload(self):
        other = make_user('rahul')
        self.client.force_authenticate(self.user)
        self.client.post('/blog/', {'title': 'New', 'content': 'B', 'author': other.pk}, format='json')
        self.assertEqual(Post.objects.get(title='New').author, self.user)

    def test_create_validation(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/blog/', {'content': 'y'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/blog/', {'title': 'x'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/blog/', {'title': 'x' * 101, 'content': 'y'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/blog/', {'title': '', 'content': 'y'}, format='json').status_code, 400)


class PostDetailTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.other = make_user('rahul')
        self.post = Post.objects.create(title='Hello', content='World', author=self.user)
        self.url = f'/blog/{self.post.pk}/'

    def test_detail_is_public(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['title'], 'Hello')

    def test_detail_not_found(self):
        self.assertEqual(self.client.get('/blog/9999/').status_code, 404)

    def test_owner_can_patch(self):
        self.client.force_authenticate(self.user)
        res = self.client.patch(self.url, {'title': 'Edited'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Edited')

    def test_owner_can_put(self):
        self.client.force_authenticate(self.user)
        res = self.client.put(self.url, {'title': 'T', 'content': 'C'}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_owner_can_delete(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_anonymous_cannot_modify(self):
        self.assertEqual(self.client.patch(self.url, {'title': 'x'}, format='json').status_code, 401)
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_cannot_edit_others_post(self):
        self.client.force_authenticate(self.other)
        res = self.client.patch(self.url, {'title': 'Hacked'}, format='json')
        self.assertEqual(res.status_code, 404)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Hello')

    def test_cannot_delete_others_post(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(self.url).status_code, 404)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_patch_cannot_change_author(self):
        self.client.force_authenticate(self.user)
        self.client.patch(self.url, {'author': self.other.pk}, format='json')
        self.post.refresh_from_db()
        self.assertEqual(self.post.author, self.user)


# ---------------------------------------------------------------- COMMENTS
class CommentTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.other = make_user('rahul')
        self.post = Post.objects.create(title='Hello', content='World', author=self.user)
        self.url = f'/blog/{self.post.pk}/comment/'

    def test_create_requires_login(self):
        res = self.client.post(self.url, {'content': 'hi'}, format='json')
        self.assertEqual(res.status_code, 401)

    def test_create_comment(self):
        self.client.force_authenticate(self.other)
        res = self.client.post(self.url, {'content': 'hi'}, format='json')
        self.assertEqual(res.status_code, 201)
        c = Comment.objects.get()
        self.assertEqual((c.author, c.post, c.content), (self.other, self.post, 'hi'))

    def test_create_comment_on_missing_post(self):
        self.client.force_authenticate(self.other)
        res = self.client.post('/blog/9999/comment/', {'content': 'hi'}, format='json')
        self.assertEqual(res.status_code, 404)

    def test_create_comment_empty_content(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.url, {'content': ''}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 400)

    def test_owner_can_delete_comment(self):
        c = Comment.objects.create(post=self.post, author=self.other, content='x')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(f'/comment/{c.pk}/delete/').status_code, 204)
        self.assertEqual(Comment.objects.count(), 0)

    def test_cannot_delete_others_comment(self):
        c = Comment.objects.create(post=self.post, author=self.other, content='x')
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(f'/comment/{c.pk}/delete/').status_code, 404)
        self.assertEqual(Comment.objects.count(), 1)

    def test_delete_requires_login(self):
        c = Comment.objects.create(post=self.post, author=self.other, content='x')
        self.assertEqual(self.client.delete(f'/comment/{c.pk}/delete/').status_code, 401)


# ---------------------------------------------------------------- LIKES
class LikeTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.other = make_user('rahul')
        self.post = Post.objects.create(title='Hello', content='World', author=self.user)
        self.url = f'/blog/{self.post.pk}/like/'

    def test_requires_login(self):
        self.assertEqual(self.client.post(self.url).status_code, 401)

    def test_toggle(self):
        self.client.force_authenticate(self.other)
        r1 = self.client.post(self.url)
        self.assertEqual(r1.data['message'], 'Liked!')
        self.assertEqual(Like.objects.filter(post=self.post).count(), 1)
        r2 = self.client.post(self.url)
        self.assertEqual(r2.data['message'], 'Unliked!')
        self.assertEqual(Like.objects.filter(post=self.post).count(), 0)

    def test_two_users_like_independently(self):
        self.client.force_authenticate(self.user); self.client.post(self.url)
        self.client.force_authenticate(self.other); self.client.post(self.url)
        self.assertEqual(Like.objects.filter(post=self.post).count(), 2)
        self.client.post(self.url)  # rahul unlike
        self.assertEqual(Like.objects.filter(post=self.post).count(), 1)

    def test_like_missing_post(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post('/blog/9999/like/').status_code, 404)

    def test_total_likes_in_detail(self):
        Like.objects.create(post=self.post, user=self.other)
        self.assertEqual(self.client.get(f'/blog/{self.post.pk}/').data['total_likes'], 1)

    def test_get_not_allowed(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 405)


# ---------------------------------------------------------------- USER POSTS
class UserPostListTests(APITestCase):
    def setUp(self):
        self.user = make_user('sumit')
        self.other = make_user('rahul')
        self.admin = User.objects.create_superuser('admin', password=STRONG_PW)
        Post.objects.create(title='mine', content='x', author=self.user)
        Post.objects.create(title='theirs', content='x', author=self.other)

    def test_requires_login(self):
        self.assertEqual(self.client.get('/blog/user/sumit/').status_code, 401)

    def test_user_sees_own_posts_only(self):
        self.client.force_authenticate(self.user)
        res = self.client.get('/blog/user/sumit/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([p['title'] for p in res.data['results']], ['mine'])

    def test_user_cannot_see_others(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get('/blog/user/rahul/').status_code, 403)

    def test_superuser_can_see_anyone(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get('/blog/user/rahul/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([p['title'] for p in res.data['results']], ['theirs'])

    def test_user_posts_pagination_is_ordered(self):
        import warnings
        from django.core.paginator import UnorderedObjectListWarning
        for i in range(12):
            Post.objects.create(title=f'p{i}', content='x', author=self.user)
        self.client.force_authenticate(self.user)
        with warnings.catch_warnings():
            warnings.simplefilter('error', UnorderedObjectListWarning)
            res = self.client.get('/blog/user/sumit/')
        self.assertEqual(res.status_code, 200)


# ---------------------------------------------------------------- DOCS
class SchemaTests(APITestCase):
    def test_schema_generates(self):
        self.assertEqual(self.client.get('/api/schema/').status_code, 200)