# from django.http import HttpResponse
# from django.shortcuts import render
# from .models import ArticlePost
# # Create your views here.
# def article_list(request):
# 	articles = ArticlePost.objects.all()
# 	context = { 'articles': articles}
# 	return render(request, 'article/list.html', context)
import markdown
from django.shortcuts import render, redirect
# 导入数据模型ArticlePost
from .models import ArticlePost
from django.http import HttpResponse
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from .models import ArticleColumn
from comment.forms import CommentForm
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView


# 列出所有文章视图
def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')
    # 初始化查询集
    article_list = ArticlePost.objects.all()
    # 用户搜索逻辑,搜索条件分为三种，按文章所属栏目查询，全文检索，按文章标签查询
    if search:
        # 用 Q对象 进行联合搜索
        article_list = article_list.filter(
            Q(title__icontains=search) |
            Q(body__icontains=search)
        )
    else:
        # 将 search 参数重置为空
        search = ''
    # 栏目查询集
    if column is not None and column.isdigit():
        print(column)
        article_list = article_list.filter(column=column)

    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')

    paginator = Paginator(article_list, 5)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    # 需要传递给模板（templates）的对象
    context = {
        'articles': articles,
        'order': order,
        'search': search,
        'column': column,
        'tag': tag,
    }
    return render(request, 'article/list.html', context)



# 查看相应文章视图
def article_detail(request, id):
    # 取出相应的文章
    # article = ArticlePost.objects.get(id=id)
    article = get_object_or_404(ArticlePost, id=id)
    # 取出文章评论
    comments = Comment.objects.filter(article=id)
    # 浏览量加1
    article.total_views += 1
    article.save(update_fields=['total_views'])
    # article.body = markdown.markdown(article.body,
    # 修改Markdown 语法渲染
    md = markdown.Markdown(
        extensions=[
         # 包含 缩写、表格等常用扩展
         'markdown.extensions.extra',
         # 语法高亮扩展
         'markdown.extensions.codehilite',
         # 扩展目录
         'markdown.extensions.toc',

        ])
    article.body = md.convert(article.body)
    # 引入评论表单
    comment_form = CommentForm()

    # 需要传递给模板的对象
    context = {'article': article, 'toc': md.toc, 'comments': comments, 'comment_form': comment_form}
    # 载入模板，并返回context对象
    return render(request, 'article/detail.html', context)


# 写文章视图
@login_required(login_url='/userprofile/login/')
def article_create(request):
    # judge person to submit message or not
    if request.method == "POST":
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            # create user and deliver its id
            new_article.author = User.objects.get(id=request.user.id)

            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])

            # save the new passage
            new_article.save()
            # save the relationship of tags
            article_post_form.save_m2m()
            # back to passage list
            return redirect("article:article_list")
        else:
            return HttpResponse("表单内容有误，请重新填写。")
    # if request is GET,return a form object for user to fill
    else:
        # create forms example
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = { 'article_post_form': article_post_form, 'columns': columns }
        return render(request, 'article/create.html', context)


# delete passage
# 装饰语句过滤未登录的用户
@login_required(login_url='/userprofile/login/')
def article_delete(request, id):
    article = ArticlePost.objects.get(id=id)
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    else:
        article.delete()
        return redirect("article:article_list")


# delete passage in safe way
@login_required(login_url='/userprofile/login/')
def article_safe_delete(request, id):
    if request.method == 'POST':
        article = ArticlePost.objects.get(id=id)
        if request.user != article.author and not request.user.is_superuser:
            return HttpResponse("抱歉，你无权修改这篇文章。")
        else:
            article.delete()
            return redirect("article:article_list")
    else:
        return HttpResponse("仅允许post请求")


# update passage
@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    """
        更新文章的视图函数
        通过POST方法提交表单，更新titile、body字段
        GET方法进入初始表单页面
        id： 文章的 id
    """
    # 获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)
    if request.user != article.author:
        return HttpResponse("抱歉，你无权修改这篇文章。")
    else:

        # 判断用户是否为 POST 提交表单数据
        if request.method == "POST":
            # 将提交的数据赋值到表单实例中
            print(article.tags.names())
            article_post_form = ArticlePostForm(data=request.POST)
            # 判断提交的数据是否满足模型的要求
            if article_post_form.is_valid():

                # 保存新写入的 title、body 数据并保存
                article.title = request.POST['title']
                article.body = request.POST['body']
                if request.POST['column'] != 'none':
                    article.column = ArticleColumn.objects.get(id=request.POST['column'])
                else:
                    article.column = None
                if request.FILES.get('avatar'):
                    article.avatar = request.FILES.get('avatar')
                article.tags.set(*request.POST.get('tags').split(','), clear=True)
                article.save()
                # 完成后返回到修改后的文章中。需传入文章的 id 值
                return redirect("article:article_detail", id=id)
            # 如果数据不合法，返回错误信息
            else:
                return HttpResponse("表单内容有误，请重新填写。")

        # 如果用户 GET 请求获取数据
        else:
            # 创建表单类实例
            article_post_form = ArticlePostForm()
            # 赋值上下文，将 article 文章对象也传递进去，以便提取旧的内容
            columns = ArticleColumn.objects.all()
            context = {
                'article': article,
                'article_post_form': article_post_form,
                'columns': columns,
                'tags': ','.join([x for x in article.tags.names()]),
            }
            # 将响应返回到模板中
            return render(request, 'article/update.html', context)


# 点赞数 +1
class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = ArticlePost.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')

