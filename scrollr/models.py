from django.db import models
from urllib.parse import quote


class Post(models.Model):
    path = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=512, blank=True, default="")
    category = models.CharField(max_length=255, blank=True, default="General", db_index=True)
    is_vid = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False, db_index=True)

    @property
    def url(self):
        return f"/media/{quote(self.path, safe='/')}"
