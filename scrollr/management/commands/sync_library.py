from django.core.management.base import BaseCommand

from scrollr.models import Media
from scrollr.views import get_library_root


VIDEO_EXTENSIONS = (".mp4", ".m4v", ".webm", ".mov", ".mkv", ".avi")
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS + PHOTO_EXTENSIONS + (".gif",)


class Command(BaseCommand):
    help = "Update the media index from the active library folder."

    def handle(self, *args, **options):
        media_folder = get_library_root()
        if not media_folder.exists():
            self.stdout.write(f"The media folder was not found: {media_folder}")
            return

        found_paths = []
        for file_path in media_folder.rglob("*"):
            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            relative_path = file_path.relative_to(media_folder).as_posix()
            relative_category = file_path.parent.relative_to(media_folder)
            category = relative_category.parts[0] if relative_category.parts else "General"
            found_paths.append(relative_path)
            Media.objects.update_or_create(
                path=relative_path,
                defaults={
                    "title": file_path.stem[:512],
                    "category": category[:255],
                    "is_vid": extension in VIDEO_EXTENSIONS,
                },
            )

        if found_paths:
            Media.objects.exclude(path__in=found_paths).delete()
        else:
            Media.objects.all().delete()
        self.stdout.write(f"Synced {len(found_paths)} media files from {media_folder}.")
