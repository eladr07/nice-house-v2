from django.urls import path

from . import views

urlpatterns = [
    path('cci/', views.MadadBIListView.as_view(), name='contruction-cost-list'),
    path('cci/add', views.MadadBICreate.as_view()),
    path('cci/<int:pk>', views.MadadBIUpdate.as_view()),
    path('cci/<int:pk>/del', views.MadadBIDelete.as_view()),
    
    path('cpi/', views.MadadCPListView.as_view(), name='consumer-price-list'),
    path('cpi/add', views.MadadCPCreate.as_view()),
    path('cpi/<int:pk>', views.MadadCPUpdate.as_view()),
    path('cpi/<int:pk>/del', views.MadadCPDelete.as_view()),
    
    path('tax/', views.TaxListView.as_view(), name='tax-list'),
    path('tax/add', views.TaxCreate.as_view()),
    path('tax/<int:pk>', views.TaxUpdate.as_view()),
    path('tax/<int:pk>/del', views.TaxDelete.as_view()),
]