from django.urls import path
from . import views
from django.contrib import admin

admin.site.index_title = 'Chatops administration'

urlpatterns = [
    path('', views.index, name='index')
]
