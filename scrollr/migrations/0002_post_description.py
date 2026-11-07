from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scrollr", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
