from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('category', models.CharField(choices=[('PRINTING', 'Printing'), ('SCANNING', 'Scanning'), ('GOVERNMENT', 'Government Services'), ('INTERNET', 'Internet & Email'), ('FINANCIAL', 'Financial Services'), ('DOCUMENTS', 'Documents & Certificates'), ('PHONE', 'Phone Services'), ('OTHER', 'Other')], db_index=True, default='OTHER', max_length=30)),
                ('stock', models.PositiveIntegerField(default=9999)),
                ('is_service', models.BooleanField(default=True)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
