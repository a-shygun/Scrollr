import hashlib

from django.core.paginator import Paginator
from django.core.management import call_command
from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from pathlib import Path

from yourstagram.models import Media


def index(request, category="", vote=""):
    if not Media.objects.exists() and settings.MEDIA_ROOT.is_dir():
        call_command("sync_library", str(settings.MEDIA_ROOT))

    available_media_types = set(
        Media.objects.order_by().values_list("media_type", flat=True).distinct()
    )
    media_type_labels = (
        ("video", "videos", "Videos"),
        ("photo", "photos", "Photos"),
        ("gif", "gifs", "GIFs"),
    )
    type_options = [
        {"name": label, "value": value}
        for media_type, value, label in media_type_labels
        if media_type in available_media_types
    ]
    show_type_filter = len(type_options) > 1

    categories = list(
        Media.objects.order_by().values_list("category", flat=True)
        .distinct().order_by("category")
    )
    category_name = next((name for name in categories if slugify(name) == category), "")
    if category == "all":
        category_name = ""

    vote_filter = vote or "all"
    type_filter = request.GET.get("type", "all")
    if type_filter not in {option["value"] for option in type_options}:
        type_filter = "all"
    query = request.GET.get("q", "").strip()

    media = Media.objects.all()
    if category_name:
        media = media.filter(category=category_name)
    if vote_filter == "all":
        media = media.exclude(vote_choice="dislike")
    else:
        media = media.filter(vote_choice=vote_filter)

    media_types = {value: media_type for media_type, value, _ in media_type_labels}
    if type_filter in media_types:
        media = media.filter(media_type=media_types[type_filter])
    if query:
        media = media.filter(Q(title__icontains=query) | Q(category__icontains=query))

    media = list(media.order_by("category", "title", "path"))
    media.sort(key=lambda item: hashlib.blake2b(
        f"1000:{item.path}".encode(), digest_size=8
    ).digest())
    page_obj = Paginator(media, 100).get_page(request.GET.get("page"))

    category_options = [{"name": "All categories", "value": "", "url": f"/all/{vote}/" if vote else "/all/"}]
    category_options += [
        {"name": name, "value": name, "url": f"/{slugify(name)}/{vote}/" if vote else f"/{slugify(name)}/"}
        for name in categories
    ]

    category_path = category or "all"
    vote_options = [{"name": "All votes", "value": "all", "url": f"/{category_path}/"}]
    vote_options += [
        {"name": choice.title(), "value": choice, "url": f"/{category_path}/{choice}/"}
        for choice in ("like", "dislike")
    ]
    return render(request, "yourstagram/index.html", {
        "page_obj": page_obj,
        "category_options": category_options,
        "vote_options": vote_options,
        "type_options": type_options,
        "show_type_filter": show_type_filter,
        "query": query,
        "selected_category": category_name,
        "selected_vote": vote_filter,
        "vote_filter": vote_filter,
        "type_filter": type_filter,
        "page_range": page_obj.paginator.get_elided_page_range(page_obj.number),
        "can_choose_library": settings.DEBUG,
        "library_path": str(current_library_path()),
        "sync_status": request.GET.get("sync", ""),
    })


def current_library_path():
    if settings.LIBRARY_PATH_FILE.exists():
        return Path(settings.LIBRARY_PATH_FILE.read_text().strip()).expanduser()
    return settings.MEDIA_ROOT


@require_POST
def sync_library_view(request):
    folder = request.POST.get("folder", "").strip()
    if folder:
        call_command("sync_library", folder)
    return redirect("/?sync=done")


def media_file(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    file_path = current_library_path() / media.path
    if not file_path.is_file():
        raise Http404
    return FileResponse(file_path.open("rb"))


@require_POST
def cast_vote(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    choice = request.POST.get("choice")
    if choice in ("like", "dislike"):
        media.vote_choice = None if media.vote_choice == choice else choice
        media.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"vote": media.vote_choice})
    return redirect(request.META.get("HTTP_REFERER", "/"))
