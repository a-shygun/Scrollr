import hashlib
import mimetypes
import os
from pathlib import Path

from django.core.paginator import Paginator
from django.core.management import call_command
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from scrollr.models import Media


def get_library_root():
    if settings.DEBUG:
        try:
            configured_path = (Path(__file__).resolve().parents[1] / ".library_path").read_text().strip()
            if configured_path:
                library_root = Path(configured_path).expanduser().resolve(strict=True)
                if library_root.is_dir() and os.access(library_root, os.R_OK | os.X_OK):
                    return library_root
        except (OSError, RuntimeError, ValueError):
            pass
    return settings.DATA_ROOT.resolve()


def local_return_url(request):
    target = request.POST.get("return_to") or request.META.get("HTTP_REFERER", "/")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return "/"
    return target


def index(request, category="", vote=""):
    library_root = get_library_root()
    local_library_enabled = settings.DEBUG and request.META.get("REMOTE_ADDR") in {"127.0.0.1", "::1"}

    categories = list(
        Media.objects.order_by().values_list("category", flat=True)
        .distinct().order_by("category")
    )
    category = request.GET.get("category", category)
    vote = request.GET.get("vote", vote)
    category_name = next((name for name in categories if slugify(name) == category), "")
    if category == "all":
        category_name = ""

    vote_filter = vote or "all"
    query = request.GET.get("q", "").strip()

    media = Media.objects.all()
    if category_name:
        media = media.filter(category=category_name)
    if vote_filter == "all":
        media = media.exclude(vote_choice="dislike")
    else:
        media = media.filter(vote_choice=vote_filter)

    if query:
        media = media.filter(Q(title__icontains=query) | Q(category__icontains=query))

    media = list(media.order_by("category", "title", "path"))
    media.sort(key=lambda item: hashlib.blake2b(
        f"1000:{item.path}".encode(), digest_size=8
    ).digest())
    page_obj = Paginator(media, 100).get_page(request.GET.get("page"))
    return render(request, "scrollr/index.html", {
        "page_obj": page_obj,
        "category_options": [{"name": "All categories", "value": "all"}] + [
            {"name": name, "value": slugify(name)} for name in categories
        ],
        "vote_options": [{"name": "All votes", "value": "all"}] + [
            {"name": choice.title(), "value": choice} for choice in ("like", "dislike")
        ],
        "query": query,
        "selected_category": category_name,
        "selected_category_slug": slugify(category_name) if category_name else "all",
        "selected_vote": vote_filter,
        "return_url": request.get_full_path(),
        "local_library_enabled": local_library_enabled,
        "custom_library_path": str(library_root) if library_root != settings.DATA_ROOT.resolve() else "",
        "page_range": page_obj.paginator.get_elided_page_range(page_obj.number),
    })


def _parse_byte_range(value, size):
    """Return an inclusive (start, end) range, or None for invalid requests."""
    try:
        unit, range_spec = value.strip().split("=", 1)
        if unit.strip() != "bytes" or "," in range_spec:
            return None
        first, last = range_spec.strip().split("-", 1)
        if first:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1
        else:
            suffix_length = int(last)
            if suffix_length <= 0:
                return None
            start, end = max(0, size - suffix_length), size - 1
        return (start, end) if 0 <= start < size and start <= end else None
    except (ValueError, TypeError):
        return None


def _stream_file_range(file_path, start, length):
    with file_path.open("rb") as media_file_obj:
        media_file_obj.seek(start)
        remaining = length
        while remaining:
            chunk = media_file_obj.read(min(64 * 1024, remaining))
            if not chunk:
                return
            remaining -= len(chunk)
            yield chunk


def media_file(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    library_root = get_library_root()
    file_path = (library_root / media.path).resolve()
    if not file_path.is_relative_to(library_root):
        raise Http404
    if not file_path.is_file():
        raise Http404

    size = file_path.stat().st_size
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    range_header = request.headers.get("Range", "")
    if range_header:
        byte_range = _parse_byte_range(range_header, size)
        if byte_range is None:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            response["Accept-Ranges"] = "bytes"
            return response

        start, end = byte_range
        length = end - start + 1
        response = StreamingHttpResponse(
            _stream_file_range(file_path, start, length), status=206, content_type=content_type
        )
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
    else:
        response = FileResponse(file_path.open("rb"), content_type=content_type)

    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_POST
def cast_vote(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    choice = request.POST.get("choice")
    if choice in ("like", "dislike"):
        media.vote_choice = choice
        media.save(update_fields=["vote_choice"])
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"choice": choice})
        messages.success(request, "Saved to liked posts" if choice == "like" else "Hidden from your feed")
    else:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Invalid vote"}, status=400)
        messages.error(request, "That vote could not be saved.")

    return redirect(local_return_url(request))


@require_POST
def set_library_path(request):
    if not settings.DEBUG or request.META.get("REMOTE_ADDR") not in {"127.0.0.1", "::1"}:
        raise Http404

    selected_path = request.POST.get("path", "").strip()
    config_file = Path(__file__).resolve().parents[1] / ".library_path"
    if selected_path:
        try:
            library_root = Path(selected_path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError, ValueError):
            messages.error(request, "Try again.")
            return redirect(local_return_url(request))

        config_file.write_text(str(library_root))
        success_message = f"Using local media folder: {library_root}"
    else:
        config_file.unlink(missing_ok=True)
        success_message = "Using the bundled demo library."

    call_command("sync_library")
    messages.success(request, success_message)
    return redirect(local_return_url(request))
