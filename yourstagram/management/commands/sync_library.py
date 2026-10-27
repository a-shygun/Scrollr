from django.conf import settings
from django.core.management.base import BaseCommand

from yourstagram.models import Media


VIDEO_EXTENSIONS = (".mp4", ".m4v", ".webm", ".mov", ".mkv", ".avi")
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


class Command(BaseCommand):
    help = "Update the Media table from the media folder."

    def handle(self, *args, **options):
        media_folder = settings.MEDIA_ROOT
        if not media_folder.exists():
            self.stdout.write(f"The media folder was not found: {media_folder}")
            return

        found_paths = []

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
        self.stdout.write(f"Synced {len(found_paths)} media files.")
