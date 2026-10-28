from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from scrollr.views import cast_vote, index, media_file, set_library_path


urlpatterns = [
    path("", index, name="index"),
    path("all/", index, {"category": "all"}, name="all_categories"),
    path("vote/<int:media_id>/", cast_vote, name="vote"),
    path("media/<int:media_id>/", media_file, name="media_file"),
]

if settings.DEBUG:
    urlpatterns.append(path("local-library/", set_library_path, name="set_library_path"))
    urlpatterns += staticfiles_urlpatterns()

urlpatterns += [
    path("<slug:category>/", index, name="category"),
    path("<slug:category>/<slug:vote>/", index, name="category_vote"),
]
