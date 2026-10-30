from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from scrollr.models import Post

VIDEO_EXTENSIONS = {".mp4", ".m4v", ".webm", ".mov", ".mkv", ".avi"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class Command(BaseCommand):
    help = "Add media files from DATA_ROOT that are not in the database yet."

    def handle(self, *args, **options):
        root = settings.DATA_ROOT.resolve()
        if not root.is_dir():
            raise CommandError(f"Media folder not found: {root}")

        added = 0
        for file in root.rglob("*"):
            if not file.is_file() or file.suffix.lower() not in MEDIA_EXTENSIONS:
                continue

            relative = file.relative_to(root).as_posix()
            parts = file.relative_to(root).parts
            _, created = Post.objects.get_or_create(
                path=relative,
                defaults={
                    "title": file.stem,
                    "category": parts[0] if len(parts) > 1 else "General",
                    "is_vid": file.suffix.lower() in VIDEO_EXTENSIONS,
                },
            )
            added += created

        self.stdout.write(f"Added {added} media files from {root}.")
