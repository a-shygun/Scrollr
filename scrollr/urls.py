from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from scrollr.views import delete_media, index, toggle_favorite


urlpatterns = [
    path("", index, name="index"),
    path("favorite/<path:path>/", toggle_favorite, name="favorite"),
    path("delete/<path:path>/", delete_media, name="delete_post"),
]
urlpatterns += staticfiles_urlpatterns()
