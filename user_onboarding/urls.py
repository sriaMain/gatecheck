from django.urls import path
from .views import CreateUserAPIView, CompanyAPIView, UserProfileAPIView



urlpatterns = [
    path('create-user/', CreateUserAPIView.as_view(), name='create-user'),
    path('create-user/<int:id>/', CreateUserAPIView.as_view(), name='user-detail'),
    path('company/', CompanyAPIView.as_view(), name='company-info'),
    path('company/<int:id>/', CompanyAPIView.as_view(), name='company-detail'),
    path('profile/',UserProfileAPIView.as_view(), name='user-profile'),
    
]
