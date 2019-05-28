# Generated by Django 2.2.1 on 2019-05-27 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionUpdateHistory',
            fields=[
                ('tid', models.AutoField(primary_key=True, serialize=False)),
                ('transaction_type', models.PositiveIntegerField(verbose_name='transaction_type')),
                ('transaction_id', models.PositiveIntegerField(verbose_name='transaction_id')),
                ('field_name', models.TextField(verbose_name='field_name')),
                ('field_value', models.TextField(verbose_name='field_value')),
                ('timestamp', models.DateTimeField(verbose_name='timestamp')),
            ],
            options={
                'db_table': 'TransactionUpdateHistory',
            },
        ),
        migrations.AddField(
            model_name='demand',
            name='not_yet_paid',
            field=models.IntegerField(default=0, editable=False),
        ),
    ]