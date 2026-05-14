from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('pay/<str:token>/', views.mock_payment_gate, name='mock_payment_gate'),
    path('pay/<str:token>/success/', views.payment_success, name='payment_success')
]