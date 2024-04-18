from django.urls import path
from . import views

app_name = 'comment'

urlpatterns = [
    # 发表评论
    # 一级评论
    path('post-comment/<int:article_id>/', views.post_comment, name='post_comment'),
    # 二级评论
    path('post-comment/<int:article_id>/<int:parent_comment_id>', views.post_comment, name='comment_reply'),
    # 评论删除
    path('comment_delete/<int:article_id>/<int:comment_id>/', views.comment_delete, name='comment_delete'),
    # 修改评论
    path('comment_edit/<int:article_id>/<int:comment_id>/', views.comment_edit, name='comment_edit'),

]