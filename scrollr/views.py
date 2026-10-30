from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from scrollr.models import Post


def index(request):
    posts = Post.objects.all().order_by("path")
    categories = list(
        posts.order_by().values_list("category", flat=True).distinct().order_by("category")
    )
    selected = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()

    if selected == "favorites":
        posts = posts.filter(is_favorite=True)
    elif selected:
        posts = posts.filter(category=selected)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(category__icontains=query))

    page_obj = Paginator(posts, 50).get_page(request.GET.get("page"))
    bundled = (settings.BASE_DIR / "data").resolve()
    return render(request, "scrollr/index.html", {
        "page_obj": page_obj,
        "category_options": [
            {"name": "All categories", "value": ""},
            {"name": "Favorites", "value": "favorites"},
        ] + [{"name": name, "value": name} for name in categories],
        "query": query,
        "selected_category": selected,
        "can_delete_posts": settings.DATA_ROOT.resolve() != bundled,
        "page_range": page_obj.paginator.get_elided_page_range(page_obj.number),
    })


@require_POST
def toggle_favorite(request, path):
    post, _ = Post.objects.get_or_create(path=path)
    post.is_favorite = not post.is_favorite
    post.save(update_fields=["is_favorite"])
    return JsonResponse({"favorite": post.is_favorite})


@require_POST
def delete_media(request, path):
    try:
        (settings.DATA_ROOT / path).unlink(missing_ok=True)
    except OSError:
        return JsonResponse({"error": "Could not delete the media file"}, status=500)
    Post.objects.filter(path=path).delete()
    return JsonResponse({"deleted": True})
