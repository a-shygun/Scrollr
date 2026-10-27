from django.conf import settings
from django.core.management.base import BaseCommand
from pathlib import Path

from yourstagram.models import Media


VIDEO_EXTENSIONS = (".mp4", ".m4v", ".webm", ".mov", ".mkv", ".avi")
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


class Command(BaseCommand):
    help = "Update the Media table from the media folder."

    def add_arguments(self, parser):
        parser.add_argument("folder", nargs="?", help="Folder containing category folders and media files")

    def handle(self, *args, **options):
        media_folder = Path(options["folder"] or settings.MEDIA_ROOT).expanduser().resolve()
        if not media_folder.exists():
            self.stdout.write(f"The media folder was not found: {media_folder}")
            return

        found_paths = []

        media_files = []
        for file_path in media_folder.rglob("*"):
            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            if extension in VIDEO_EXTENSIONS:
                media_type = "video"
            elif extension == ".gif":
                media_type = "gif"
            elif extension in PHOTO_EXTENSIONS:
                media_type = "photo"
            else:
                continue

            relative_path = file_path.relative_to(media_folder).as_posix()
            media_files.append((file_path, relative_path, media_type))

        if not media_files:
            self.stdout.write("No supported media files found.")
            return

        if options["folder"] and hasattr(settings, "LIBRARY_PATH_FILE"):
            settings.LIBRARY_PATH_FILE.write_text(str(media_folder))

        for file_path, relative_path, media_type in media_files:
            found_paths.append(relative_path)
            Media.objects.update_or_create(
                path=relative_path,
                defaults={
                    "title": file_path.stem[:512],
                    "category": file_path.parent.name[:255],
                    "media_type": media_type,
                },
            )

        Media.objects.exclude(path__in=found_paths).delete()
        self.stdout.write(f"Synced {len(found_paths)} media files from {media_folder}.")
