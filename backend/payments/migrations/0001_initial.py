from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(choices=[('MPESA', 'M-PESA'), ('CASH', 'Cash')], max_length=20)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('change_due', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('checkout_request_id', models.CharField(blank=True, db_index=True, max_length=120, null=True)),
                ('merchant_request_id', models.CharField(blank=True, max_length=120, null=True)),
                ('mpesa_receipt_number', models.CharField(blank=True, max_length=120, null=True)),
                ('result_code', models.CharField(blank=True, max_length=20, null=True)),
                ('result_description', models.TextField(blank=True, null=True)),
                ('mpesa_transaction_date', models.CharField(blank=True, max_length=30, null=True)),
                ('raw_callback', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='sales.sale')),
            ],
        ),
    ]
