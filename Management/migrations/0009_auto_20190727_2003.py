# Generated by Django 2.2.3 on 2019-07-27 20:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Management', '0008_auto_20190724_0842'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name='employeecheck',
                    name='checkbase_ptr',
                ),
                migrations.RemoveField(
                    model_name='employeecheck',
                    name='employee',
                ),
                migrations.RemoveField(
                    model_name='employeecheck',
                    name='purpose_type',
                ),
                migrations.RemoveField(
                    model_name='paymentcheck',
                    name='account',
                ),
                migrations.RemoveField(
                    model_name='paymentcheck',
                    name='checkbase_ptr',
                ),
                migrations.RemoveField(
                    model_name='paymentcheck',
                    name='supplier_type',
                ),
                migrations.DeleteModel(
                    name='CheckBase',
                ),
                migrations.DeleteModel(
                    name='CheckBaseType',
                ),
                migrations.DeleteModel(
                    name='EmployeeCheck',
                ),
                migrations.DeleteModel(
                    name='ExpenseType',
                ),
                migrations.DeleteModel(
                    name='PaymentCheck',
                ),
                migrations.DeleteModel(
                    name='PurposeType',
                ),
                migrations.DeleteModel(
                    name='SupplierType',
                ),
            ],
        ),
    ]