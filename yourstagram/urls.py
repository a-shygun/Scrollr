from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from yourstagram.views import cast_vote, index, media_file, sync_library_view


urlpatterns = [
    path("", index, name="index"),
    path("all/", index, {"category": "all"}, name="all_categories"),
    path("vote/<int:media_id>/", cast_vote, name="vote"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [
        path("sync-library/", sync_library_view, name="sync_library"),
        path("media/<int:media_id>/", media_file, name="media_file"),
    ]

urlpatterns += [
    path("<slug:category>/", index, name="category"),
    path("<slug:category>/<slug:vote>/", index, name="category_vote"),
]
