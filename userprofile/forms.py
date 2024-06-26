# 引入表单类
from django import forms
# 引入 User 模型
from django.contrib.auth.models import User
# 引入 Profile 模型
from .models import Profile


# 登录表单，继承了 forms.Form 类
class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()


# 注册用表单
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField()
    password2 = forms.CharField()

    class Meta:
        model = User
        fields = ('username', 'email')

    # 对两次输入的密码是否一致进行检查
    # 验证密码一致性方法不能写def clean_password()，
    # 因为如果你不定义def clean_password2()方法，
    # 会导致password2中的数据被Django判定为无效数据从而清洗掉，
    # 从而password2属性不存在。最终导致两次密码输入始终会不一致，并且很难判断出错误原因。
    def clean_password2(self):
        data = self.cleaned_data
        if data.get('password') == data.get('password2'):
            return data.get('password')
        else:
            raise forms.ValidationError("密码输入不一致,请重试。")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone', 'avatar', 'bio')