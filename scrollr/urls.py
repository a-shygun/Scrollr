from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from scrollr.views import delete_media, index, serve_media, toggle_favorite


urlpatterns = [
    path("", index, name="index"),
    path("media/<path:path>", serve_media, name="media"),
    path("favorite/<path:path>/", toggle_favorite, name="favorite"),
    path("delete/<path:path>/", delete_media, name="delete_post"),
]
urlpatterns += staticfiles_urlpatterns()
