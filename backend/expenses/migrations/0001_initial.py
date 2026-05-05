from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('category', models.CharField(choices=[('RENT', 'Rent'), ('INTERNET', 'Internet'), ('ELECTRICITY', 'Electricity'), ('PAPER', 'Printing Paper'), ('TONER', 'Toner/Ink'), ('WAGES', 'Employee Wages'), ('TRANSPORT', 'Transport'), ('MAINTENANCE', 'Maintenance'), ('OTHER', 'Other')], db_index=True, max_length=30)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('CASH', 'Cash'), ('MPESA', 'M-PESA'), ('BANK', 'Bank'), ('OTHER', 'Other')], default='CASH', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
