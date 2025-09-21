from django.urls import path
from authen.views import  ActivateAccountView
from .views import signup, handlelogin, handlelogout

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', handlelogin, name='handlelogin'),
    path('logout/', handlelogout, name='handlelogout'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
]
