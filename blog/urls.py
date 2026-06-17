from django.urls import path
from . import views

urlpatterns = [
    path('',views.blog,name="blog"),
    path('blog/', views.PostListCreateView.as_view(), name='list_create'),
    
    # ← pehle specific
    path('blog/user/<str:username>/', views.UserPostListView.as_view(), name='user_posts'),
    
    # ← baad mein dynamic
    path('blog/<int:pk>/', views.PostDetailView.as_view(), name='delete-update'),
    
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Like & Comment
    path('blog/<int:pk>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('blog/<int:pk>/like/', views.LikeToggleView.as_view(), name='like_toggle'),
]