from django.db import models


class Media(models.Model):
    path = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=512)
    category = models.CharField(max_length=255, db_index=True)
    is_vid = models.BooleanField(default=False)
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
        return f"/media/{self.id}/"

