from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from scrollr.views import delete_media, index, serve_media, shuffle_posts, toggle_favorite


urlpatterns = [
    path("", index, name="index"),
    path("shuffle/", shuffle_posts, name="shuffle_posts"),
    path("media/<path:path>", serve_media, name="media"),
    path("favorite/<path:path>/", toggle_favorite, name="favorite"),
    path("delete/<path:path>/", delete_media, name="delete_post"),
]
urlpatterns += staticfiles_urlpatterns()
