from django.urls import path
from .views import order_detail
urlpatterns = [path('orders/<int:id>/', order_detail)]
