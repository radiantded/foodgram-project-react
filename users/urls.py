from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/', views.Login.as_view(), name='login'),
    path('password_change/', views.PassChange.as_view(), name='password_change'),
    path('pass_change_done/', views.PassChangeDone.as_view(), name='pass_change_done'),
    path('password_reset/', views.PassReset.as_view(), name='password_reset'),
    path('pass_reset_done/', views.PassResetDone.as_view(), name='pass_reset_done'),
    path('pass_reset_confirm/<uidb64>/<token>/', views.PassResetConfirm.as_view(), name='pass_reset_confirm'),
    path('pass_reset_complete/', views.PassResetComplete.as_view(), name='pass_reset_complete')
]
