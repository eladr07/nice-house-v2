from django.urls import path

from . import views

urlpatterns = [
    path('saleanalysis/', views.sale_analysis, name='sale-analysis'),
    path('nhseasonprofit/', views.nh_season_profit, name='nh-season-profit'),
    path('seasonincome/', views.season_income, name='season-income'),
    path('profitloss', views.global_profit_lost, name='profit-loss'),
    path('projectsprofit', views.projects_profit, name='projects-profit'),
]