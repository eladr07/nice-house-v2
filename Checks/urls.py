from django.urls import path

from . import views

urlpatterns = [
    path('checks/', views.check_list, name='checks-list'),
    path('checks/add', views.check_add, name='checks-add'),
    path('checks/<int:id>', views.check_edit),
    path('checks/<int:pk>/del', views.PaymentCheckDelete.as_view()),
         
    path('employeechecks/', views.employeecheck_list, name='employee-checks-list'),
    path('employeechecks/add', views.employeecheck_add, name='employee-checks-add'),
    path('employeechecks/<int:id>', views.employeecheck_edit),
    path('employeechecks/<int:id>/del', views.EmployeeCheckDelete.as_view()),
]