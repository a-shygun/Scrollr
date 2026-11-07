from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import json

from scrollr.models import Post

VIDEO_EXTENSIONS = {".mp4", ".m4v", ".webm", ".mov", ".mkv", ".avi"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def video_description(file):
    """Read the description stored by common downloaders or media containers."""
    info_file = file.with_suffix(".info.json")
    if info_file.is_file():
        try:
            description = json.loads(info_file.read_text(encoding="utf-8")).get("description")
            if isinstance(description, str):
                return description
        except (OSError, json.JSONDecodeError):
            pass

    # Sidecar text files are useful for libraries whose metadata is maintained manually.
    text_file = file.with_suffix(".description")
    if text_file.is_file():
        try:
            return text_file.read_text(encoding="utf-8")
        except OSError:
            pass
    return ""


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
            defaults = {
                "title": file.stem,
                "category": parts[0] if len(parts) > 1 else "General",
                "is_vid": file.suffix.lower() in VIDEO_EXTENSIONS,
                "description": video_description(file) if file.suffix.lower() in VIDEO_EXTENSIONS else "",
            }
            post, created = Post.objects.get_or_create(
                path=relative,
                defaults=defaults,
            )
            if not created and post.is_vid and defaults["description"] != post.description:
                post.description = defaults["description"]
                post.save(update_fields=["description"])
            added += created

        self.stdout.write(f"Added {added} media files from {root}.")
