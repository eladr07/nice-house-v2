"""NiceHouse URL Configuration

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
from django.contrib import admin, auth
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]

from Management.models import *
from Management.views import *
import Management.forms

urlpatterns += [
    path('', index),
    path('locatehouse', locate_house),
    path('locatedemand', locate_demand),
    
    path('contacts/', ContactListView.as_view()),
    path('contact/add', ContactCreate.as_view()),
    path('contact/<int:pk>', ContactUpdate.as_view()),
    path('contact/<int:id>/del', contact_delete),

    path('projects/', ProjectListView.as_view()),
    path('projects/pdf', project_list_pdf),
    path('projects/archive', ProjectArchiveListView.as_view()),
    
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
    path('projects/<int:project_id>/contacts/<int:id>/del', contact_delete),
    path('projects/<int:id>/', project_edit),
    path('projectcommission/<int:pk>', ProjectCommissionUpdate.as_view()),
    path('projects/add/', project_add),
    path('projects/end/<int:pk>', ProjectEndUpdate.as_view()),
    path('projects/<int:project_id>/buildings', project_buildings),
    path('projects/<int:project_id>/buildings/add', building_add),
    
    path('buildings/<int:pk>', BuildingUpdate.as_view()),
    path('buildings/<int:object_id>/clients/', building_clients),
    path('buildings/<int:object_id>/clients/pdf', building_clients_pdf),
    path('buildings/<int:building_id>/addparking', building_addparking),
    path('buildings/<int:building_id>/addstorage', building_addstorage),
    path('buildings/<int:object_id>/pricelist/type<int:type_id>', building_pricelist),
    path('buildings/<int:building_id>/pricelist/type<int:type_id>/house/<int:house_id>/del', house_delete),
    path('buildings/<int:object_id>/pricelist/type<int:type_id>/pdf', building_pricelist_pdf),
    path('buildings/<int:building_id>/addhouse/type<int:type_id>', building_addhouse),
    path('buildings/<int:building_id>/house/<int:id>/type<int:type_id>', house_edit),
    path('buildings/<int:building_id>/house/<int:id>/type<int:type_id>/versionlog', house_version_log),
    path('buildings/<int:building_id>/copy', building_copy),
    path('buildings/<int:building_id>/del', building_delete),

    path('projects/<int:project_id>/<commission>/', project_commission_add),
    path('projects/<int:project_id>/<commission>/del', project_commission_del),

    path('projects/<int:id>/addinvoice', project_invoice_add),
    path('projects/<int:id>/addpayment', project_payment_add),
    
    path('projects/<int:project_id>/demands/notyetpaid', project_demands,
     {'func':'demands_not_yet_paid', 'template_name' : 'Management/project_demands_noinvoice.html'}),
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
     
    path('parkings/<int:pk>', ParkingUpdate.as_view()),
    path('storages/<int:pk>', StorageUpdate.as_view()),
        
    path('employees/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':Employee}),
    path('employees/<int:obj_id>/attachments', obj_attachments,
     {'model':Employee}),
    path('employees/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':Employee}),
    path('employees/<int:obj_id>/reminders', obj_reminders,
     {'model': Employee}),
    path('employees/<int:object_id>/loans', employee_loans),
    path('employees/<int:employee_id>/addloan', employee_addloan),
    path('employees/<int:employee_id>/loanpay', employee_loanpay),
    path('employees/<int:employee_id>/<commission>/project/<int:project_id>', employee_commission_add),
    path('employees/<int:employee_id>/<commission>/project/<int:project_id>/del', employee_commission_del),    
    path('employees/<int:employee_id>/addproject', employee_project_add),
    path('employees/<int:employee_id>/removeproject/<int:project_id>', employee_project_remove),
    path('employees/', EmployeeListView.as_view()),
    path('employees/pdf', employee_list_pdf),
    path('employees/archive', EmployeeArchiveListView.as_view()),
    path('employees/add/', EmployeeCreate.as_view()),
    path('employees/<int:pk>/', EmployeeUpdate.as_view()),
    path('employees/end/<int:object_id>', employee_end),
    path('employees/<int:id>/employmentterms', employee_employmentterms,
     {'model':EmployeeBase}),
    path('employees/<int:id>/account', employee_account,
     {'model':EmployeeBase}),

    # NOT USED 
    path('accounts/<int:pk>/', AccountUpdate.as_view()),
     
    path('epcommission/<int:pk>', EPCommissionUpdate.as_view()),

    path('nhemployees/<int:obj_id>/attachment/add', obj_add_attachment,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/attachments', obj_attachments,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/addreminder', obj_add_reminder,
     {'model':EmployeeBase}),
    path('nhemployees/<int:obj_id>/reminders', obj_reminders,
     {'model': EmployeeBase}),
    path('nhemployees/<int:object_id>/loans', employee_loans),
    path('nhemployees/<int:employee_id>/addloan', nhemployee_addloan),
    path('nhemployees/<int:employee_id>/loanpay', nhemployee_loanpay),
    path('nhemployees/add/', nhemployee_add),
    # NOT USED 
    path('nhemployees/<int:pk>/', NHEmployeeUpdate.as_view()),
    # NOT USED 
    path('nhemployees/end/<int:pk>/', NHEmployeeEndUpdate.as_view()),
    path('nhemployees/<int:id>/employmentterms', employee_employmentterms,
     {'model':EmployeeBase}),
    path('nhemployees/<int:id>/account', employee_account,
     {'model':EmployeeBase}),
     
    path('nhcbi/add', NHCommissionCreate.as_view()),
    path('nhcbi/<int:pk>', NHCommissionUpdate.as_view()),
    path('nhcbi/<int:pk>/del', NHCommissionDelete.as_view()),
          
    path('reminder/<int:pk>', ReminderUpdate.as_view()),
    path('reminder/<int:id>/del', reminder_del),
    path('reminder/<int:id>/do', reminder_do),

    path('attachments', attachment_list),
    path('attachment/add', attachment_add),
    path('attachment/<int:pk>', AttachmentUpdate.as_view()),
    path('attachment/<int:pk>/del', AttachmentDelete.as_view()),

    path('tasks/', task_list),
    path('task/add', task_add),
    path('task/<int:pk>/del', TaskDelete.as_view()),
    path('task/<int:id>/do', task_do),

    path('links/', LinkListView.as_view()),
    path('link/add', LinkCreate.as_view()),
    path('link/<int:pk>', LinkUpdate.as_view()),
    path('link/<int:pk>/del', LinkDelete.as_view()),
     
    path('cars/', CarListView.as_view()),
    path('car/add', CarCreate.as_view()),
    path('car/<int:object_id>', CarUpdate.as_view()),
    path('car/<int:object_id>/del', CarDelete.as_view()),
    
    path('nhbranch/add', NHBranchCreate.as_view()),
    path('nhbranch/<int:pk>/', NHBranchUpdate.as_view()),

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

    path('salaryexpenses/', SalaryExpensesListView.as_view()),
    path('nhsalaryexpenses/', NHSalaryExpensesListView.as_view()),
    path('salaryexpenses/<int:id>/approve', salary_expenses_approve),
    path('salaryexpenses/<int:pk>', SalaryExpensesUpdate.as_view()),
     path('salary/<int:salary_id>/expenses', employee_salary_expenses),
     
    path('employeesalaries/', employee_salary_list),
    path('employeesalaryseason/', employeesalary_season_list),
    path('esseasontotalexpenses/', employeesalary_season_total_expenses, name='salary-season-total-expenses'),
    path('esseasonexpenses/', employeesalary_season_expenses, name='salary-season-expenses'),

    path('employeesalaries/<int:year>/<int:month>/pdf', employee_salary_pdf),
    path('employeesalaries/<int:pk>', EmployeeSalaryUpdate.as_view()),
    path('employeesalaries/<int:id>/calc', employee_salary_calc,
     {'model':EmployeeSalary}),
    path('employeesalaries/<int:id>/delete', employee_salary_delete,
     {'model':EmployeeSalary}),
    path('employeesalaries/<int:pk>/details', EmployeeSalaryCommissionDetailView.as_view()),
    path('employeesalaries/<int:pk>/checkdetails', EmployeeSalaryCheckDetailView.as_view()),
    path('employeesalaries/<int:pk>/totaldetails', EmployeeSalaryTotalDetailView.as_view()),
    path('employeesalaries/<int:id>/approve', employee_salary_approve),
    path('employees/<int:id>/sales/<int:year>/<int:month>', employee_sales),
    
    path('employee/remarks/<int:year>/<int:month>', employee_remarks),
    path('employee/refund/<int:year>/<int:month>', employee_refund),
    
    path('nhemployeesalaries/', nhemployee_salary_list),
    path('nhemployeesalaries/<int:nhbranch_id>/<int:year>/<int:month>/pdf', nhemployee_salary_pdf),
    path('nhemployeesalaries/<int:nhbranch_id>/<int:year>/<int:month>/send', nhemployee_salary_send),
    path('nhemployeesalaries/<int:pk>', NHEmployeeSalaryUpdate.as_view()),
    path('nhemployeesalaries/<int:id>/calc', employee_salary_calc,
     {'model':NHEmployeeSalary}),
    path('nhemployeesalaries/<int:id>/delete', employee_salary_delete,
     {'model':NHEmployeeSalary}),
    path('nhemployeesalaries/<int:object_id>/details', NHEmployeeSalaryCommissionDetailView.as_view()),
    path('nhemployeesalaries/<int:pk>/checkdetails', NHEmployeeSalaryCheckDetailView.as_view()),
    path('nhemployeesalaries/<int:pk>/totaldetails', NHEmployeeSalaryTotalDetailView.as_view()),
    path('nhemployeesalaries/<int:id>/approve', employee_salary_approve),
    path('nhemployee/<int:id>/sales/<int:year>/<int:month>', nhemployee_sales),
    
    path('nhemployee/remarks/<int:year>/<int:month>', nhemployee_remarks),
    path('nhemployee/refund/<int:year>/<int:month>', nhemployee_refund),
        
    path('payments/add', payment_add),
    path('payments/<int:pk>', PaymentUpdate.as_view()),
    path('payments/<int:id>/del', payment_del),
    
    path('invoices/add', invoice_add),      
    path('invoices/<int:pk>', InvoiceUpdate.as_view()),
    path('invoices/<int:id>/del', invoice_del),
     
    path('invoices/<int:id>/offset', invoice_offset),   
    path('invoices/offset', invoice_offset),      
    path('invoiceoffset/<int:pk>', InvoiceOffsetUpdate.as_view()),
    path('invoiceoffset/<int:id>/del', invoice_offset_del),
    
    path('checks/', check_list),
    path('checks/add', check_add),
    path('checks/<int:id>', check_edit),
    path('checks/<int:pk>/del', PaymentCheckDelete.as_view()),
        
    path('advancepayments', AdvancePaymentListView.as_view()),
    path('advancepayments/add', AdvancePaymentCreate.as_view()),
    path('advancepayments/<int:pk>', AdvancePaymentUpdate.as_view()),
    path('advancepayments/<int:id>/toloan', advance_payment_toloan),
    path('advancepayments/<int:pk>/del', AdvancePaymentDelete.as_view()),
    
    path('loans/', LoanListView.as_view()),
    path('loans/add', LoanCreate.as_view()),
    path('loans/<int:pk>', LoanUpdate.as_view()),
    path('loans/<int:pk>/del', LoanDelete.as_view()),
     
    path('loanpays/<int:pk>', LoanPayUpdate.as_view()),
    
    path('lawyers/', LawyerListView.as_view()),
    path('lawyers/add', LawyerCreate.as_view()),
    path('lawyers/<int:pk>', LawyerUpdate.as_view()),
    path('lawyers/<int:pk>/del', LawyerDelete.as_view()),
    
    path('incomes/', income_list),
    path('incomes/add', income_add),
    path('incomes/<int:id>', income_edit),
    path('incomes/<int:pk>/del', IncomeDelete.as_view()),
     
    path('employeechecks/', employeecheck_list),
    path('employeechecks/add', employeecheck_add),
    path('employeechecks/<int:id>', employeecheck_edit),
    path('employeechecks/<int:id>/del', EmployeeCheckDelete.as_view()),
    
    path('reports/project_month/<int:project_id>/<int:year>/<int:month>', report_project_month),
    path('reports/projects_month/<int:year>/<int:month>', report_projects_month),
    path('reports/project_season/<int:project_id>/<int:from_year>/<int:from_month>/<int:to_year>/<int:to_month>', report_project_season),
    path('reports/project_followup/<int:project_id>/<int:from_year>/<int:from_month>/<int:to_year>/<int:to_month>', report_project_followup),
    path('reports/employeesales', report_employee_sales),
    
    path('madadbi/', MadadBIListView.as_view()),
    path('madadbi/add', MadadBICreate.as_view()),
    path('madadbi/<int:pk>', MadadBIUpdate.as_view()),
    path('madadbi/<int:pk>/del', MadadBIDelete.as_view()),
    
    path('madadcp/', MadadCPListView.as_view()),
    path('madadcp/add', MadadCPCreate.as_view()),
    path('madadcp/<int:pk>', MadadCPUpdate.as_view()),
    path('madadcp/<int:pk>/del', MadadCPDelete.as_view()),
    
    path('tax/', TaxListView.as_view()),
    path('tax/add', TaxCreate.as_view()),
    path('tax/<int:pk>', TaxUpdate.as_view()),
    path('tax/<int:pk>/del', TaxDelete.as_view()),
    
    path('salepricemod/<int:pk>', SalePriceModUpdate.as_view()),
    path('salehousemod/<int:pk>', SaleHouseModUpdate.as_view()),
    path('salepre/<int:object_id>', salepaymod_edit, {'model' : SalePre}),
    path('salereject/<int:object_id>', salepaymod_edit, {'model' : SaleReject}),
    path('salecancel/<int:pk>', SaleCancelUpdate.as_view()),
      
    path('nhbranch/<int:branch_id>/nhsale/add', nhsale_add),
    path('nhbranch/<int:nhbranch_id>/addnhemployee', NHBranchEmployeeCreate.as_view()),
    path('nhbranchemployee/<int:pk>', NHBranchEmployeeUpdate.as_view()),
    path('nhsale/<int:pk>/', NHSaleDetailView.as_view()),
    path('nhsale/<int:object_id>/move', nhsale_move_nhmonth),
    path('nhsale/<int:pk>/edit', NHSaleUpdate.as_view()),
    path('nhsaleside/<int:object_id>', NHSaleSideUpdate.as_view()),
    path('nhsaleside/<int:object_id>/payment/add', nhsaleside_payment_add),
    path('nhsaleside/<int:object_id>/invoice/add', nhsaleside_invoice_add),
    
    path('mail', send_mail),
]

urlpatterns += [
    path('demands/<int:id>/zero', demand_zero),
    path('demands/<int:id>/forcefullypaid', demand_force_fully_paid),
    path('demands/<int:id>/notyetpaid', demand_not_yet_paid),
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
    path('demands/<int:demand_id>/sale/<int:id>/del', demand_sale_del),
    path('demands/<int:demand_id>/sale/<int:id>/reject', demand_sale_reject),
    path('demands/<int:demand_id>/sale/<int:id>/pre', demand_sale_pre),
    path('demands/<int:demand_id>/sale/<int:id>/cancel', demand_sale_cancel),
    path('demands/<int:id>/invoice/add', demand_invoice_add),
    path('demands/<int:id>/payment/add', demand_payment_add),
    path('demandinvoice/<int:id>', demand_invoice_edit),
    path('demandpayment/<int:id>', demand_payment_edit),
    path('demands/<int:id>/close', demand_close),
    path('demands/<int:pk>/remarks', DemandRemarksUpdate.as_view()),
    path('demands/<int:pk>/salecount', DemandSaleCountUpdate.as_view()),
    path('demands/<int:object_id>/adddiff', demand_adddiff),
    path('demands/<int:object_id>/adddiffadjust', demand_adddiff_adjust),
    path('demanddiff/<int:pk>', DemandDiffUpdate.as_view()),
    path('demanddiff/<int:pk>/del', demanddiff_del),
          
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
    path('house_details/<int:pk>', HouseDetailView.as_view()),
    # NOT USED
    path('signup_details/<int:pk>', SignupDetailView.as_view()),
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
    path('activity/<int:pk>/', ActivityDetailView.as_view()),
    path('activity/<int:pk>/edit', ActivityUpdate.as_view()),    
]