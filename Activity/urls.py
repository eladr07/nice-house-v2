from django.urls import path

from . import views

urlpatterns = [
    path('activitybase/<int:activitybase_id>/citycallers/add', views.activitybase_citycallers_add, name='city-callers-add'),
    path('citycallers/<int:object_id>', views.citycallers_edit, name='city-callers-edit'),

    path('activitybase/<int:activitybase_id>/mediareferrals/add', views.activitybase_mediareferrals_add, name='media-referrals-add'),
    path('mediareferrals/<int:object_id>', views.mediareferrals_edit, name='media-referrals-edit'),

    path('activitybase/<int:activitybase_id>/event/add', views.activitybase_event_add, name='event-add'),
    path('event/<int:object_id>', views.event_edit, name='event-edit'),

    path('activitybase/<int:activitybase_id>/priceoffer/add', views.activitybase_priceoffer_add, name='price-offer-add'),
    path('priceoffer/<int:object_id>', views.priceoffer_edit, name='price-offer-edit'),

    path('activitybase/<int:activitybase_id>/saleprocess/add', views.activitybase_saleprocess_add, name='sale-process-add'),
    path('saleprocess/<int:object_id>', views.saleprocess_edit, name='sale-process-edit'),
    
    path('activity/add', views.activity_add),
    path('activity/<int:pk>/', views.ActivityDetailView.as_view()),
    path('activity/<int:pk>/edit', views.ActivityUpdate.as_view()),  
]