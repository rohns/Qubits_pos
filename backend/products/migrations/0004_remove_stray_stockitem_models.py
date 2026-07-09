from django.db import migrations


class Migration(migrations.Migration):
    """
    Removes StockItem, StockItemMovement, and ServiceRecipe — these were
    mistakenly included in migration 0003 from an earlier delivery. They were
    never part of products/models.py in your actual codebase and nothing
    references them, so this just drops three empty, unused tables. No data
    loss: these tables have no rows and nothing reads from or writes to them.
    """

    dependencies = [
        ('products', '0003_stockitem_stockitemmovement_servicerecipe'),
    ]

    operations = [
        # Delete in FK-dependency order: children before parents.
        migrations.DeleteModel(name='ServiceRecipe'),
        migrations.DeleteModel(name='StockItemMovement'),
        migrations.DeleteModel(name='StockItem'),
    ]
