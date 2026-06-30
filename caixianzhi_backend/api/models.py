# 导入 Django 提供的模型基类
from django.db import models

# 导入 Django 自带的用户模型
from django.contrib.auth.models import User

# 导入模型信号 post_save，用于在用户保存后触发事件
from django.db.models.signals import post_save

# 导入信号接收器装饰器
from django.dispatch import receiver

# ------------------------------
# 创建用户扩展信息模型 Profile
# ------------------------------
class Profile(models.Model):
    # 定义性别选项的可选值（元组列表）
    GENDER_CHOICES = (
        ('男', '男'),
        ('女', '女'),
        ('保密', '保密'),
    )

    # 与 User 模型建立一对一关系，每个用户有唯一一个 Profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # 性别字段，最大长度为2，使用 choices 限定可选值，默认是“保密”
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, default='保密')

    # 头像字段，图片上传到 avatars/ 目录下，允许为空（null）或不填（blank）
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # 返回用户名字符串，便于后台展示
    def __str__(self):
        return self.user.username

# ---------------------------------------------
# 使用信号：在创建 User 实例后自动创建 Profile 实例
# ---------------------------------------------
@receiver(post_save, sender=User)  # 当 User 模型 post_save 事件触发时调用该函数
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # 如果是新创建的用户
        Profile.objects.create(user=instance)  # 自动为其创建对应的 Profile
