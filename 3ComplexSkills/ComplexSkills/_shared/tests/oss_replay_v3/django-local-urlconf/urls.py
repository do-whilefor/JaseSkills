from django.urls import path
urlpatterns=[path('api/projects/<int:id>/', views.project)]
