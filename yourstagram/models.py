from urllib.parse import quote

from django.conf import settings
from django.db import models


class Media(models.Model):
    path = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=512)
    category = models.CharField(max_length=255, db_index=True)
    media_type = models.CharField(
        max_length=8,
        choices=[("video", "Video"), ("photo", "Photo"), ("gif", "GIF")],
        db_index=True,
    )
    vote_choice = models.CharField(
        max_length=7,
        choices=[("like", "Like"), ("dislike", "Dislike")],
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        ordering = ["category", "title", "path"]
        verbose_name_plural = "media"

    @property
    def url(self):
        if settings.DEBUG:
            return f"/media/{self.id}/"
        return "/static/media/" + quote(self.path, safe="/")

    @property
    def type(self):
        return "video" if self.media_type == "video" else "image"
