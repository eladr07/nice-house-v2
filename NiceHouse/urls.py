﻿"""NiceHouse URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
]

from Management.models import *
from Management.views import *
import Management.forms

urlpatterns = [
    path('accounts/login/', django.contrib.auth.views.login),
    path('accounts/logout/', django.contrib.auth.views.logout),
    path('accounts/password_change/', django.contrib.auth.views.password_change),
]

urlpatterns += [
    path('', index),
    path('locatehouse', locate_house),
    path('locatedemand', locate_demand),
    
    path('contacts/', limited_object_list,
     {'queryset' : Contact.objects.all(), 'template_name' : 'Management/contact_list.html'}),
    path('contact/add', limited_create_object,
     {'form_class' : Management.forms.ContactForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '.'}),
    path('contact/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.ContactForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('contact/<int:id>/del', contact_delete),
    path('projects/', project_list),
    path('projects/pdf', project_list_pdf),
    path('projects/archive', limited_object_list,
     {'queryset':Project.objects.archive(), 'template_name':'Management/project_archive.html'}),
    path('projects/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':Project}),
    path('projects/<int:obj_id>/reminders', obj_reminders,
     {'model':Project}),
    path('projects/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':Project}),
    path('projects/<int:obj_id>/attachments', obj_attachments,
     {'model':Project}),
    path('projects/<int:project_id>/addcontact', project_contact),
    path('projects/<int:project_id>/contact/<int:id>/remove', project_removecontact),
    path('projects/<int:project_id>/contact/<int:id>/delete', project_deletecontact),
    path('projects/<int:project_id>/demandcontact', project_contact, {'demand':True}),
    path('projects/<int:project_id>/paymentcontact', project_contact, {'payment':True}),
    path('projects/\d+/contacts/<int:id>/del', contact_delete),
    path('projects/<int:id>/', project_edit),
    path('projectcommission/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.ProjectCommissionForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('projects/add/', project_add),
    path('projects/end/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.ProjectEndForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('projects/<int:project_id>/buildings', project_buildings),
    path('projects/<int:project_id>/buildings/add', building_add),
    path('buildings/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.BuildingForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('buildings/<int:object_id>/clients/', building_clients),
    path('buildings/<int:object_id>/clients/pdf', building_clients_pdf),
    path('buildings/<int:building_id>/addparking', building_addparking),
    path('buildings/<int:building_id>/addstorage', building_addstorage),
    path('buildings/<int:object_id>/pricelist/type<int:type_id>', building_pricelist),
    path('buildings/<int:building_id>/pricelist/type<int:type_id>/house/<int:house_id>/del', house_delete),
    path('buildings/<int:object_id>/pricelist/type<int:type_id>/pdf', building_pricelist_pdf),
    path('buildings/<int:building_id>/addhouse/type<int:type_id>', building_addhouse),
    path('buildings/\d+/house/<int:id>/type<int:type_id>', house_edit),
    path('buildings/\d+/house/<int:id>/type<int:type_id>/versionlog', house_version_log),
    path('buildings/<int:building_id>/copy', building_copy),
    path('buildings/<int:building_id>/del', building_delete),
    path('projects/<int:project_id>/<commission>/', project_commission_add),
    path('projects/<int:project_id>/<commission>/del', project_commission_del),

    path('projects/<int:id>/addinvoice', project_invoice_add),
    path('projects/<int:id>/addpayment', project_payment_add),
    
    path('projects/<int:project_id>/demands/unpaid', project_demands, 
     {'func':'demands_unpaid', 'template_name' : 'Management/project_demands_unpaid.html'}),
    path('projects/<int:project_id>/demands/noinvoice', project_demands, 
     {'func':'demands_noinvoice', 'template_name' : 'Management/project_demands_noinvoice.html'}),
    path('projects/<int:project_id>/demands/nopayment', project_demands, 
     {'func':'demands_nopayment', 'template_name' : 'Management/project_demands_nopayment.html'}),
    path('projects/<int:project_id>/demands/mispaid', project_demands, 
     {'func':'demands_mispaid', 'template_name' : 'Management/project_demands_mispaid.html'}),
    path('demandsall', demands_all),
    
    path('projectsprofit', projects_profit),
    
    path('buildings/add', building_add),
     
    path('parkings/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.ParkingForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('storages/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.StorageForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
        
    path('employees/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':Employee}),
    path('employees/<int:obj_id>/attachments', obj_attachments,
     {'model':Employee}),
    path('employees/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':Employee}),
    path('employees/<int:obj_id>/reminders', obj_reminders,
     {'model': Employee}),
    path('employees/<int:object_id>/loans', limited_object_detail,
     {'queryset':Employee.objects.all(), 'template_name':'Management/employee_loans.html', 'template_object_name':'employee'}),
    path('employees/<int:employee_id>/addloan', employee_addloan),
    path('employees/<int:employee_id>/loanpay', employee_loanpay),
    path('employees/<int:employee_id>/<commission>/project/<int:project_id>', employee_commission_add),
    path('employees/<int:employee_id>/<commission>/project/<int:project_id>/del', employee_commission_del),    
    path('employees/<int:employee_id>/addproject', employee_project_add),
    path('employees/<int:employee_id>/removeproject/<int:project_id>', employee_project_remove),
    path('employees/', employee_list),
    path('employees/pdf', employee_list_pdf),
    path('employees/archive', limited_object_list,
     {'queryset':Employee.objects.archive(), 'template_name':'Management/employee_archive.html', 'template_object_name':'employee',
      'extra_context':{'nhbranch_list':NHBranch.objects.all()}}),
    path('employees/add/', limited_create_object,
     {'form_class' : Management.forms.EmployeeForm, 'post_save_redirect' : '/employees/%(id)s'}),
    path('employees/<int:object_id>/', limited_update_object,
     {'form_class' : Management.forms.EmployeeForm, 'post_save_redirect' : '/employees/%(id)s'}),
    path('employees/end/<int:object_id>', employee_end),
    path('employees/<int:id>/employmentterms', employee_employmentterms,
     {'model':EmployeeBase}),
    path('employees/<int:id>/account', employee_account,
     {'model':EmployeeBase}),
     
    path('accounts/<int:object_id>/', limited_update_object,
     {'form_class' : Management.forms.AccountForm, 'post_save_redirect' : '%(id)s'}),
     
     path('epcommission/<int:object_id>', limited_update_object,
     {'model' : EPCommission, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),

     path('nhemployees/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/attachments', obj_attachments,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/reminders', obj_reminders,
     {'model': EmployeeBase}),
    path('nhemployees/<int:object_id>/loans', limited_object_detail,
     {'queryset':NHEmployee.objects.all(), 'template_name':'Management/employee_loans.html', 'template_object_name':'employee'}),
    path('nhemployees/<int:employee_id>/addloan', nhemployee_addloan),
    path('nhemployees/<int:employee_id>/loanpay', nhemployee_loanpay),
    path('nhemployees/add/', nhemployee_add),
    path('nhemployees/<int:object_id>/', limited_update_object,
     {'form_class' : Management.forms.NHEmployeeForm, 'post_save_redirect' : '/nhemployees/%(id)s'}),
    path('nhemployees/end/<int:id>/', limited_update_object,
     {'form_class' : Management.forms.EmployeeEndForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhemployees/<int:id>/employmentterms', employee_employmentterms,
     {'model':EmployeeBase}),
    path('nhemployees/<int:id>/account', employee_account,
     {'model':EmployeeBase}),
     
    path('nhcbi/add', limited_create_object,
     {'form_class' : Management.forms.NHCommissionForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhcbi/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.NHCommissionForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhcbi/<int:object_id>/del', limited_delete_object,
     {'form_class' : Management.forms.NHCommissionForm, 'post_delete_redirect':'/nhemployee/%(nhemployee_id)'}),
          
    path('reminder/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.ReminderForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('reminder/<int:id>/del', reminder_del),
    path('reminder/<int:id>/do', reminder_do),
    path('attachments', attachment_list),
    path('attachment/add', attachment_add),
    path('attachment/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.AttachmentForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('attachment/<int:id>/del', attachment_delete),
    path('tasks/', task_list),
    path('task/add', task_add),
    path('task/<int:object_id>/del', limited_delete_object,
     {'model':Task, 'post_delete_redirect':'/tasks'}),
    path('task/<int:id>/do', task_do),
    path('links/', limited_object_list,
     {'queryset': Link.objects.all()}),
    path('link/add', limited_create_object,
     {'model' : Management.models.Link, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('link/<int:object_id>', limited_update_object,
     {'model' : Management.models.Link, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('link/<int:object_id>/del', limited_delete_object,
     {'model':Link, 'post_delete_redirect':'/links'}),
    path('cars/', limited_object_list,
     {'queryset': Car.objects.all()}),
    path('car/add', limited_create_object,
     {'model' : Management.models.Car, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('car/<int:object_id>', limited_update_object,
     {'model' : Management.models.Car, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('car/<int:object_id>/del', limited_delete_object,
     {'model':Car, 'post_delete_redirect':'/cars'}),
    
    path('nhbranch/add', limited_create_object,
     {'model' : Management.models.NHBranch, 'template_name' : 'Management/nhbranch_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhbranch/<int:object_id>/', limited_update_object,
     {'model' : Management.models.NHBranch, 'template_name' : 'Management/nhbranch_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhbranch/<int:nhbranch_id>/sales/', nhmonth_sales),
    path('nhmonth/close', nhmonth_close),
    path('nhseasonincome/', nh_season_income),
    path('nhseasonprofit/', nh_season_profit),
    
    path('seasonincome/', season_income),
    
    path('projects/<int:project_id>/signups/', signup_list),
    path('projects/<int:project_id>/signups/add', signup_edit),
    path('signups/<int:id>/cancel', signup_cancel),
    path('signups/<int:id>', signup_edit),
    
    path('sale', sale_add),
    path('sale/<int:id>', sale_edit),
    path('sale/<int:sale_id>/commission', salecommissiondetail_edit),
    
    path('saleanalysis/', sale_analysis),

    path('splitpayment/add', split_payment_add),

    path('salariesbank/', salaries_bank),

    path('salaryexpenses/', salary_expenses_list),
    path('nhsalaryexpenses/', nh_salary_expenses_list),
    path('salaryexpenses/<int:id>/approve', salary_expenses_approve),
    path('salaryexpenses/<int:object_id>', limited_update_object,
     {'model' : Management.models.SalaryExpenses, 'template_name' : 'Management/salaryexpenses_edit.html', 'post_save_redirect' : '%(id)s'}),
     path('salary/<int:salary_id>/expenses', employee_salary_expenses),
     
    path('employeesalaries/', employee_salary_list),
    path('employeesalaryseason/', employeesalary_season_list),
    path('esseasontotalexpenses/', employeesalary_season_total_expenses),
    path('esseasonexpenses/', employeesalary_season_expenses),
    path('employeesalaries/<int:year>/<int:month>/pdf', employee_salary_pdf),
    path('employeesalaries/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.EmployeeSalaryForm, 'template_name' : 'Management/employee_salary_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('employeesalaries/<int:id>/calc', employee_salary_calc,
     {'model':EmployeeSalary}),
    path('employeesalaries/<int:id>/delete', employee_salary_delete,
     {'model':EmployeeSalary}),
    path('employeesalaries/<int:object_id>/details', limited_object_detail,
     {'queryset':EmployeeSalary.objects.all(),
      'template_name':'Management/employee_commission_details.html',
      'template_object_name':'salary'}),
    path('employeesalaries/<int:object_id>/checkdetails', limited_object_detail,
     {'queryset':EmployeeSalary.objects.all(),
      'template_name':'Management/employee_salary_check_details.html',
      'template_object_name':'salary'}),
    path('employeesalaries/<int:object_id>/totaldetails', limited_object_detail,
     {'queryset':EmployeeSalary.objects.all(), 'template_name':'Management/employee_salary_total_details.html', 
      'template_object_name':'salary'}),
    path('employeesalaries/<int:id>/approve', employee_salary_approve),
    path('employees/<int:id>/sales/<int:year>/<int:month>', employee_sales),
    
    path('employee/remarks/<int:year>/<int:month>', employee_remarks),
    path('employee/refund/<int:year>/<int:month>', employee_refund),
    
    path('nhemployeesalaries/', nhemployee_salary_list),
    path('nhemployeesalaries/<int:nhbranch_id>/<int:year>/<int:month>/pdf', nhemployee_salary_pdf),
    path('nhemployeesalaries/<int:nhbranch_id>/<int:year>/<int:month>/send', nhemployee_salary_send),
    path('nhemployeesalaries/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.NHEmployeeSalaryForm, 'template_name' : 'Management/nhemployee_salary_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhemployeesalaries/<int:id>/calc', employee_salary_calc,
     {'model':NHEmployeeSalary}),
    path('nhemployeesalaries/<int:id>/delete', employee_salary_delete,
     {'model':NHEmployeeSalary}),
    path('nhemployeesalaries/<int:object_id>/details', limited_object_detail,
     {'queryset':NHEmployeeSalary.objects.all(), 'template_name':'Management/nhemployee_commission_details.html',
      'template_object_name':'salary'}),
    path('nhemployeesalaries/<int:object_id>/checkdetails', limited_object_detail,
     {'queryset':NHEmployeeSalary.objects.all(), 'template_name':'Management/employee_salary_check_details.html.html',
      'template_object_name':'salary'}),
    path('nhemployeesalaries/<int:object_id>/totaldetails', limited_object_detail,
     {'queryset':NHEmployeeSalary.objects.all(), 'template_name':'Management/employee_salary_total_details.html',
      'template_object_name':'salary'}),
    path('nhemployeesalaries/<int:id>/approve', employee_salary_approve),
    path('nhemployee/<int:id>/sales/<int:year>/<int:month>', nhemployee_sales),
    
    path('nhemployee/remarks/<int:year>/<int:month>', nhemployee_remarks),
    path('nhemployee/refund/<int:year>/<int:month>', nhemployee_refund),
        
    path('payments/add', payment_add),
    path('payments/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.PaymentForm, 'template_name' : 'Management/payment_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('payments/<int:id>/del', payment_del),
    
    path('invoices/add', invoice_add),      
    path('invoices/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.InvoiceForm, 'template_name' : 'Management/invoice_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('invoices/<int:id>/del', invoice_del),
     
    path('invoices/<int:id>/offset', invoice_offset),   
    path('invoices/offset', invoice_offset),      
    path('invoiceoffset/<int:object_id>', limited_update_object,
     {'model' : InvoiceOffset, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('invoiceoffset/<int:id>/del', invoice_offset_del),
    
    path('checks/', check_list),
    path('checks/add', check_add),
    path('checks/<int:id>', check_edit),
    path('checks/<int:id>/del', limited_delete_object,
     {'model':PaymentCheck, 'post_delete_redirect':'/checks'}),
        
    path('advancepayments', limited_object_list,
     {'queryset': AdvancePayment.objects.filter(is_paid=None)}),
    path('advancepayments/add', limited_create_object,
     {'form_class' : Management.forms.AdvancePaymentForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('advancepayments/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.AdvancePaymentForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('advancepayments/<int:id>/toloan', advance_payment_toloan),
    path('advancepayments/<int:id>/del', limited_delete_object,
     {'model':AdvancePayment, 'post_delete_redirect':'/advancepayments'}),
    
    path('loans/', limited_object_list,
     {'queryset': Loan.objects.all(), 'permission': 'list_loan'}),
    path('loans/add', limited_create_object,
     {'form_class' : Management.forms.LoanForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('loans/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.LoanForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('loans/<int:id>/del', limited_delete_object,
     {'model':Loan, 'post_delete_redirect':'/loans'}),
     
    path('loanpays/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.LoanPayForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    
    path('lawyers/', limited_object_list,
     {'queryset': Lawyer.objects.all()}),
    path('lawyers/add', limited_create_object,
     {'model' : Lawyer, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('lawyers/<int:object_id>', limited_update_object,
     {'model' : Lawyer, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('lawyers/<int:id>/del', limited_delete_object,
     {'model':Lawyer, 'post_delete_redirect':'/lawyers'}),
    
    path('incomes/', income_list),
    path('incomes/add', income_add),
    path('incomes/<int:id>', income_edit),
    path('incomes/<int:id>/del', limited_delete_object,
     {'model':Income, 'post_delete_redirect':'/incomes'}),
     
    path('employeechecks/', employeecheck_list),
    path('employeechecks/add', employeecheck_add),
    path('employeechecks/<int:id>', employeecheck_edit),
    path('employeechecks/<int:id>/del', limited_delete_object,
     {'model':EmployeeCheck, 'post_delete_redirect':'/employeechecks'}),
    
    path('reports/project_month/<int:project_id>/<int:year>/<int:month>', report_project_month),
    path('reports/projects_month/<int:year>/<int:month>', report_projects_month),
    path('reports/project_season/<int:project_id>/<int:from_year>/<int:from_month>/<int:to_year>/<int:to_month>', report_project_season),
    path('reports/project_followup/<int:project_id>/<int:from_year>/<int:from_month>/<int:to_year>/<int:to_month>', report_project_followup),
    path('reports/employeesales', report_employee_sales),
    
    path('madadbi/', limited_object_list,
     {'queryset':MadadBI.objects.all(), 'template_name':'Management/madadbi_list.html'}),
    path('madadbi/add', limited_create_object,
     {'form_class' : Management.forms.MadadBIForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('madadbi/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.MadadBIForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('madadbi/<int:object_id>/del', limited_delete_object,
     {'model':MadadBI, 'post_delete_redirect':'/madadbi'}),
    
    path('madadcp/', limited_object_list,
     {'queryset':MadadCP.objects.all(), 'template_name':'Management/madadcp_list.html'}),
    path('madadcp/add', limited_create_object,
     {'form_class' : Management.forms.MadadCPForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('madadcp/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.MadadCPForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('madadcp/<int:id>/del', limited_delete_object,
     {'model':MadadCP, 'post_delete_redirect':'/madadcp'}),
    
    path('tax/', limited_object_list,
     {'queryset':Tax.objects.all(), 'template_name':'Management/tax_list.html'}),
    path('tax/add', limited_create_object,
     {'form_class' : Management.forms.TaxForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('tax/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.TaxForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('tax/<int:object_id>/del', limited_delete_object,
     {'model':Tax, 'post_delete_redirect':'/tax'}),
    
    path('salepricemod/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.SalePriceModForm, 'template_name' : 'Management/sale_mod_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('salehousemod/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.SaleHouseModForm, 'template_name' : 'Management/sale_mod_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('salepre/<int:object_id>', salepaymod_edit, {'model' : SalePre}),
    path('salereject/<int:object_id>', salepaymod_edit, {'model' : SaleReject}),
    path('salecancel/<int:object_id>', limited_update_object,
     {'model' : Management.models.SaleCancel, 'template_name' : 'Management/sale_mod_edit.html', 'post_save_redirect' : '%(id)s'}),
      
    path('nhbranch/<int:branch_id>/nhsale/add', nhsale_add),
    path('nhbranch/<int:nhbranch_id>/addnhemployee', nhbranch_add_nhemployee),
    path('nhbranchemployee/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.NHBranchEmployeeForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhsale/<int:object_id>/', nhsale_edit),
    path('nhsale/<int:object_id>/move', nhsale_move_nhmonth),
    path('nhsale/<int:object_id>/edit', limited_update_object,
     {'form_class' : Management.forms.NHSaleForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '../%(id)s'}),
    path('nhsaleside/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.NHSaleSideForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('nhsaleside/<int:object_id>/payment/add', nhsaleside_payment_add),
    path('nhsaleside/<int:object_id>/invoice/add', nhsaleside_invoice_add),
    
    (r'^mail', send_mail),
]

urlpatterns += [
    path('demands/<int:id>/zero', demand_zero),
    path('demands/<int:id>/forcefullypaid', demand_force_fully_paid),
    path('demands/<int:object_id>', demand_edit),
    path('demands/<int:obj_id>/reminders', obj_reminders,
     {'model': Demand}),
    path('demands/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':Demand}),
    path('demands/<int:id>/close', demand_close),
    path('demandsales/', demand_sale_list),
    
    path('demands/', demand_list),
    path('demands/<int:id>/calc', demand_calc),
    path('demands/<int:id>/returntocalc', demand_return_to_calc),
    path('demandsold/', demand_old_list),
    path('demandseason/', demand_season_list),
    path('demandfollowup/', demand_followup_list),
    path('demandpaybalance/', demand_pay_balance_list),
    path('demands/closeall', demand_closeall),
    path('demands/sendall', demands_send),
    path('demands/<int:demand_id>/sale/add', sale_add),
    path('demands/\d+/sale/<int:id>/del', demand_sale_del),
    path('demands/\d+/sale/<int:id>/reject', demand_sale_reject),
    path('demands/\d+/sale/<int:id>/pre', demand_sale_pre),
    path('demands/\d+/sale/<int:id>/cancel', demand_sale_cancel),
    path('demands/<int:id>/invoice/add', demand_invoice_add),
    path('demands/<int:id>/payment/add', demand_payment_add),
    path('demandinvoice/<int:id>', demand_invoice_edit),
    path('demandpayment/<int:id>', demand_payment_edit),
    path('demands/<int:id>/close', demand_close),
    path('demands/<int:object_id>/remarks', limited_update_object,
     {'form_class' : Management.forms.DemandRemarksForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : 'remarks',
      'permission':'Management.demand_remarks'}),
    path('demands/<int:object_id>/salecount', limited_update_object,
     {'form_class' : Management.forms.DemandSaleCountForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : 'salecount',
      'permission':'Management.demand_sale_count', 'extra_context':{'title':u"עדכון מס' מכירות צפוי"}}),
    path('demands/<int:object_id>/adddiff', demand_adddiff),
    path('demands/<int:object_id>/adddiffadjust', demand_adddiff_adjust),
    path('demanddiff/<int:object_id>', limited_update_object,
     {'form_class' : Management.forms.DemandDiffForm, 'template_name' : 'Management/object_edit.html', 'post_save_redirect' : '%(id)s'}),
    path('demanddiff/<int:object_id>/del', demanddiff_del),
          
    path('demandinvoices/', demand_invoice_list),
    path('demandpayments/', demand_payment_list),
    
    path('demands/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':Demand}),
    path('demands/<int:obj_id>/attachments', obj_attachments,
     {'model':Demand}),
]

urlpatterns += [
    path('xml/buildings/<int:project_id>', json_buildings),
    path('xml/employees/<int:project_id>', json_employees),
    path('xml/houses/<int:building_id>', json_houses),
    path('xml/house/<int:house_id>', json_house),
    path('json/links', json_links),
    path('demand_details/<int:project>/<int:year>/<int:month>', demand_details),
    path('demand_sales/<int:project_id>/<int:year>/<int:month>', demand_sales),
    path('invoice_details/<int:project>/<int:year>/<int:month>', invoice_details),
    path('payment_details/<int:project>/<int:year>/<int:month>', payment_details),
    path('house_details/<int:id>', house_details),
    path('signup_details/<int:house_id>', signup_details),
    path('profitloss', global_profit_lost),
]

urlpatterns += [
    path('activitybase/<int:activitybase_id>/citycallers/add', activitybase_citycallers_add),
    path('citycallers/<int:object_id>', citycallers_edit),
    path('activitybase/<int:activitybase_id>/mediareferrals/add', activitybase_mediareferrals_add),
    path('mediareferrals/<int:object_id>', mediareferrals_edit),
    path('activitybase/<int:activitybase_id>/event/add', activitybase_event_add),
    path('event/<int:object_id>', event_edit),
    path('activitybase/<int:activitybase_id>/priceoffer/add', activitybase_priceoffer_add),
    path('priceoffer/<int:object_id>', priceoffer_edit),
    path('activitybase/<int:activitybase_id>/saleprocess/add', activitybase_saleprocess_add),
    path('saleprocess/<int:object_id>', saleprocess_edit),
    
    path('activity/add', activity_add),
    path('activity/<int:object_id>/', limited_object_detail,
     {'queryset':Activity.objects.all(), 'template_name':'Management/activity_detail.html'}),
    path('activity/<int:object_id>/edit', limited_update_object,
     {'form_class' : Management.forms.ActivityForm, 'template_name' : 'Management/activity_edit.html', 'post_save_redirect' : 'edit'}),    
]