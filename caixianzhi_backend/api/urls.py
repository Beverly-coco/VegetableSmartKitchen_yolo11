from django.urls import path
from .views import (
    DetectionView,
    DatasetUploadView,
    LoginView,
    LogoutView,
    ProfileView,
    TrainView,
    TrainResultView,
    AvailableModelsView,
    AvailableDatasetsView
)

urlpatterns = [
    # 模块1：对象输入
    path('upload-single/', DetectionView.as_view(), name='upload_single'),
    path('upload-dataset/', DatasetUploadView.as_view(), name='upload_dataset'),
    path('datasets/', AvailableDatasetsView.as_view(), name='list_datasets'),
    
    # 模块3：模型训练
    path('train/', TrainView.as_view(), name='train_start'),
    path('train/result/<uuid:task_id>/', TrainResultView.as_view(), name='train_result'),
    path('train/available-models/', AvailableModelsView.as_view(), name='available_models'),

    # 用户认证与个人资料
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
] 