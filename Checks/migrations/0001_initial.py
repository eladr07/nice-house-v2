# Generated by Django 2.2.3 on 2019-07-27 20:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Management', '0009_auto_20190727_2003'),
    ]

    operations=[
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='CheckBaseType',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=20, unique=True, verbose_name='שם')),
                    ],
                    options={
                        'db_table': 'CheckBaseType',
                    },
                ),
                migrations.CreateModel(
                    name='ExpenseType',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=20, unique=True, verbose_name='שם')),
                    ],
                    options={
                        'db_table': 'ExpenseType',
                    },
                ),
                migrations.CreateModel(
                    name='PurposeType',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=20, unique=True, verbose_name='שם')),
                    ],
                    options={
                        'db_table': 'PurposeType',
                    },
                ),
                migrations.CreateModel(
                    name='SupplierType',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=20, unique=True, verbose_name='שם')),
                    ],
                    options={
                        'db_table': 'SupplierType',
                    },
                ),
                migrations.CreateModel(
                    name='CheckBase',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('num', models.IntegerField(unique=True, verbose_name="מס' שיק")),
                        ('issue_date', models.DateField(verbose_name='ת. הוצאה')),
                        ('pay_date', models.DateField(verbose_name='ת. תשלום')),
                        ('amount', models.IntegerField(verbose_name='סכום')),
                        ('remarks', models.TextField(blank=True, verbose_name='הערות')),
                        ('division_type', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, to='Management.DivisionType', verbose_name='חטיבה עסקית')),
                        ('expense_type', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, to='Checks.ExpenseType', verbose_name='סוג הוצאה')),
                        ('invoice', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='Management.Invoice')),
                        ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Checks.CheckBaseType', verbose_name='חשבונית')),
                    ],
                    options={
                        'db_table': 'CheckBase',
                        'ordering': ['division_type', 'expense_type'],
                    },
                ),
                migrations.CreateModel(
                    name='PaymentCheck',
                    fields=[
                        ('checkbase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Checks.CheckBase')),
                        ('tax_deduction_source', models.IntegerField(blank=True, null=True, verbose_name='נכוי מס במקור')),
                        ('order_verifier', models.CharField(max_length=30, verbose_name='מאשר ההזמנה')),
                        ('payment_verifier', models.CharField(max_length=30, verbose_name='מאשר התשלום')),
                        ('account', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='Management.Account')),
                        ('supplier_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Checks.SupplierType', verbose_name='ספק')),
                    ],
                    options={
                        'db_table': 'Check',
                    },
                    bases=('Checks.checkbase',),
                ),
                migrations.CreateModel(
                    name='EmployeeCheck',
                    fields=[
                        ('checkbase_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Checks.CheckBase')),
                        ('month', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12)], verbose_name='חודש')),
                        ('year', models.PositiveSmallIntegerField(choices=[(2009, 2009), (2010, 2010), (2011, 2011), (2012, 2012), (2013, 2013), (2014, 2014), (2015, 2015), (2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021), (2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026), (2027, 2027), (2028, 2028)], verbose_name='שנה')),
                        ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checks', to='Management.EmployeeBase', verbose_name='עובד')),
                        ('purpose_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Checks.PurposeType', verbose_name='מטרה')),
                    ],
                    options={
                        'db_table': 'EmployeeCheck',
                    },
                    bases=('Checks.checkbase',),
                ),
            ],
        ),
    ]
    