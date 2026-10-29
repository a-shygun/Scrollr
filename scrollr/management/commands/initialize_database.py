from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Create Scrollr's database tables and preserve media from legacy schemas."

    def handle(self, *args, **options):
        call_command(
            "migrate",
            run_syncdb=True,
            interactive=options["interactive"],
            verbosity=options["verbosity"],
        )
        self._import_legacy_media()

    def _import_legacy_media(self):
        target = "scrollr_media"
        legacy_tables = ("scrollr_media_legacy", "base_media")
        quote = connection.ops.quote_name

        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            if target not in tables:
                raise CommandError(f"Expected database table {target!r} was not created.")

            for table in legacy_tables:
                if table not in tables:
                    continue

                columns = {
                    field.name
                    for field in connection.introspection.get_table_description(cursor, table)
                }
                required = {"id", "path", "title", "category"}
                if not required.issubset(columns):
                    raise CommandError(f"Cannot import legacy table {table!r}: missing columns.")

                video_expression = (
                    quote("is_vid")
                    if "is_vid" in columns
                    else f"CASE WHEN {quote('media_type')} = 'video' THEN 1 ELSE 0 END"
                    if "media_type" in columns
                    else "0"
                )
                vote_expression = quote("vote_choice") if "vote_choice" in columns else "NULL"

                with transaction.atomic():
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {quote(target)} "
                        "(id, path, title, category, is_vid, vote_choice) "
                        f"SELECT {quote('id')}, {quote('path')}, {quote('title')}, "
                        f"{quote('category')}, {video_expression}, {vote_expression} "
                        f"FROM {quote(table)}"
                    )
                    cursor.execute(f"DROP TABLE {quote(table)}")
                self.stdout.write(f"Imported media from {table}.")
