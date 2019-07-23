from django.shortcuts import render

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import MadadBI, MadadCP, Tax
from .forms import MadadBIForm, MadadCPForm, TaxForm

### Madad BI Views ###

class MadadBIListView(LoginRequiredMixin, ListView):
    model = MadadBI

    def get_queryset(self):
        return MadadBI.objects.all()

class MadadBICreate(PermissionRequiredMixin, CreateView):
    model = MadadBI
    form_class = MadadBIForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_madadbi'

class MadadBIUpdate(PermissionRequiredMixin, UpdateView):
    model = MadadBI
    form_class = MadadBIForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_madadbi'

class MadadBIDelete(PermissionRequiredMixin, DeleteView):
    model = MadadBI
    success_url = '/madadbi'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_madadbi'

### Madad CP Views ###

class MadadCPListView(LoginRequiredMixin, ListView):
    model = MadadCP

    def get_queryset(self):
        return MadadCP.objects.all()

class MadadCPCreate(PermissionRequiredMixin, CreateView):
    model = MadadCP
    form_class = MadadCPForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_madadcp'

class MadadCPUpdate(PermissionRequiredMixin, UpdateView):
    model = MadadCP
    form_class = MadadCPForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_madadcp'

class MadadCPDelete(PermissionRequiredMixin, DeleteView):
    model = MadadCP
    success_url = '/madadcp'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_madadcp'

### Tax Views ###

class TaxListView(LoginRequiredMixin, ListView):
    model = Tax

    def get_queryset(self):
        return Tax.objects.all()

class TaxCreate(PermissionRequiredMixin, CreateView):
    model = Tax
    form_class = TaxForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_tax'

class TaxUpdate(PermissionRequiredMixin, UpdateView):
    model = Tax
    form_class = TaxForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_tax'

class TaxDelete(PermissionRequiredMixin, DeleteView):
    model = Tax
    success_url = '/tax'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_tax'