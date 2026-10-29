from django.db import migrations, models


def rename_legacy_media_table(apps, schema_editor):
    """Move the old table aside so the new app table can be created."""
    tables = schema_editor.connection.introspection.table_names()
    if "base_media" in tables and "scrollr_media_legacy" not in tables:
        quote = schema_editor.quote_name
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {quote('base_media')} RENAME TO {quote('scrollr_media_legacy')}"
            )


def restore_legacy_media_table(apps, schema_editor):
    """Copy media and votes into the new table, then remove the old table."""
    tables = schema_editor.connection.introspection.table_names()
    if "scrollr_media_legacy" not in tables:
        return

    quote = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {quote('scrollr_media')} "
            f"(id, path, title, category, is_vid, vote_choice) "
            f"SELECT id, path, title, category, is_vid, vote_choice "
            f"FROM {quote('scrollr_media_legacy')}"
        )
        cursor.execute(f"DROP TABLE {quote('scrollr_media_legacy')}")


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(rename_legacy_media_table, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Media",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("path", models.CharField(max_length=1024, unique=True)),
                ("title", models.CharField(max_length=512)),
                ("category", models.CharField(db_index=True, max_length=255)),
                ("is_vid", models.BooleanField(default=False)),
                (
                    "vote_choice",
                    models.CharField(
                        blank=True,
                        choices=[("like", "Like"), ("dislike", "Dislike")],
                        db_index=True,
                        max_length=7,
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": ["category", "title", "path"],
                "verbose_name_plural": "media",
            },
        ),
        migrations.RunPython(restore_legacy_media_table, migrations.RunPython.noop),
    ]
