from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from yourstagram.views import cast_vote, index


urlpatterns = [
    path("", index, name="index"),
    path("all/", index, {"category": "all"}, name="all_categories"),
    path("vote/<int:media_id>/", cast_vote, name="vote"),
    path("<slug:category>/", index, name="category"),
    path("<slug:category>/<slug:vote>/", index, name="category_vote"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
