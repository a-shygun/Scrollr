from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Case, IntegerField, When
from django.shortcuts import redirect
from django.http import JsonResponse
from django.shortcuts import render
from django.views.static import serve
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
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(category__icontains=query)
            | Q(description__icontains=query, is_vid=True)
        )

    shuffle_seed = request.session.get("shuffle_seed")
    if shuffle_seed is not None:
        from random import Random
        matching_ids = list(posts.values_list("id", flat=True))
        Random(shuffle_seed).shuffle(matching_ids)
        posts = posts.order_by(Case(*[When(id=post_id, then=position) for position, post_id in enumerate(matching_ids)], output_field=IntegerField()))

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


def shuffle_posts(request):
    from random import SystemRandom
    request.session["shuffle_seed"] = SystemRandom().getrandbits(64)
    return redirect(request.META.get("HTTP_REFERER", "/"))


def serve_media(request, path):
    return serve(request, path, document_root=settings.DATA_ROOT)


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
