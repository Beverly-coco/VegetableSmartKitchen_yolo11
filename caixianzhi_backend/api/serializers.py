# 导入 Django REST framework 的序列化器模块
from rest_framework import serializers
# 导入 Django 自带的 User 模型
from django.contrib.auth.models import User
# 导入自定义的用户扩展模型 Profile
from .models import Profile

# 定义用于序列化用户扩展信息（性别、头像）的序列化器
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile  # 绑定的模型类为 Profile
        fields = ['gender', 'avatar']  # 序列化的字段（性别 和 头像）

# 定义用户信息的序列化器，嵌套使用 ProfileSerializer
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()  # 嵌套序列化器：表示用户有一个 profile 子对象

    class Meta:
        model = User  # 绑定的模型类为 User
        fields = ['id', 'username', 'profile']  # 序列化字段：用户 ID、用户名 和 profile 子对象

    # 重写 update 方法，用于支持更新嵌套对象（profile）
    def update(self, instance, validated_data):
        # 更新用户的用户名字段
        instance.username = validated_data.get('username', instance.username)
        instance.save()  # 保存修改后的用户对象

        # 获取 profile 子对象中的数据
        profile_data = validated_data.get('profile')
        profile = instance.profile  # 获取当前用户的 profile 对象（通过 OneToOne 关联）

        if profile_data:
            # 更新性别字段
            profile.gender = profile_data.get('gender', profile.gender)
            # 如果头像字段存在，也进行更新
            if 'avatar' in profile_data:
                profile.avatar = profile_data.get('avatar', profile.avatar)
            # 保存修改后的 profile 对象
            profile.save()

        return instance  # 返回更新后的用户实例
