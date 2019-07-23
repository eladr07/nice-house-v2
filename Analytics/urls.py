from django.urls import path

from . import views

urlpatterns = [
    path('sale-analysis/', views.sale_analysis, name='sale-analysis'),
    path('nh-season-profit/', views.nh_season_profit, name='nh-season-profit'),
    path('season-income/', views.season_income, name='season-income'),
    path('profit-loss', views.global_profit_lost, name='profit-loss'),
    path('projects-profit', views.projects_profit, name='projects-profit'),
]