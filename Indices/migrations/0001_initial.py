# Generated by Django 2.2.3 on 2019-07-23 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations=[
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Tax',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('date', models.DateField(verbose_name='תאריך')),
                        ('value', models.FloatField(verbose_name='ערך')),
                    ],
                    options={
                        'verbose_name': 'מע"מ',
                        'db_table': 'Tax',
                        'ordering': ['-date'],
                        'get_latest_by': 'date',
                    },
                ),
                migrations.CreateModel(
                    name='MadadCP',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('year', models.PositiveSmallIntegerField(verbose_name='שנה')),
                        ('month', models.PositiveSmallIntegerField(verbose_name='חודש')),
                        ('publish_date', models.DateField(verbose_name='תאריך פרסום')),
                        ('value', models.FloatField(verbose_name='ערך')),
                    ],
                    options={
                        'db_table': 'MadadCP',
                        'ordering': ['-publish_date'],
                        'get_latest_by': 'publish_date',
                        'unique_together': {('year', 'month')},
                    },
                ),
                migrations.CreateModel(
                    name='MadadBI',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('year', models.PositiveSmallIntegerField(verbose_name='שנה')),
                        ('month', models.PositiveSmallIntegerField(verbose_name='חודש')),
                        ('publish_date', models.DateField(verbose_name='תאריך פרסום')),
                        ('value', models.FloatField(verbose_name='ערך')),
                    ],
                    options={
                        'db_table': 'MadadBI',
                        'ordering': ['-publish_date'],
                        'get_latest_by': 'publish_date',
                        'unique_together': {('year', 'month')},
                    },
                ),
            ],
        ),
    ]
