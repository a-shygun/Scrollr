import hashlib

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from yourstagram.models import Media


def index(request, category="", vote=""):
    categories = list(
        Media.objects.order_by().values_list("category", flat=True)
        .distinct().order_by("category")
    )
    category_name = next((name for name in categories if slugify(name) == category), "")
    if category == "all":
        category_name = ""

    vote_filter = vote or "all"
    type_filter = request.GET.get("type", "all")
    query = request.GET.get("q", "").strip()

    media = Media.objects.all()
    if category_name:
        media = media.filter(category=category_name)
    if vote_filter == "all":
        media = media.exclude(vote_choice="dislike")
    else:
        media = media.filter(vote_choice=vote_filter)

    media_types = {"videos": "video", "photos": "photo", "gifs": "gif"}
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
    type_options = [{"name": name, "value": value} for value, name in (
        ("videos", "Videos"), ("photos", "Photos"), ("gifs", "GIFs")
    )]

    return render(request, "yourstagram/index.html", {
        "page_obj": page_obj,
        "category_options": category_options,
        "vote_options": vote_options,
        "type_options": type_options,
        "query": query,
        "selected_category": category_name,
        "selected_vote": vote_filter,
        "vote_filter": vote_filter,
        "type_filter": type_filter,
        "page_range": page_obj.paginator.get_elided_page_range(page_obj.number),
    })


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
