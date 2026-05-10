import os
import re
import mimetypes
from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from .models import Song

# ---------- صفحه اصلی (لیست آهنگ‌ها) ----------
@cache_page(60 * 5)  # کش ۵ دقیقه
def home(request):
    song_list = Song.objects.all().order_by('title')
    paginator = Paginator(song_list, 10)  # هر صفحه ۱۰ آهنگ
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'music/home.html', {'page_obj': page_obj})

# ---------- صفحه پخش آهنگ ----------
def play_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)

    # لیست تمام شناسه‌ها به ترتیب عنوان (همان ترتیب صفحهٔ اصلی)
    ordered_ids = list(Song.objects.order_by('title').values_list('id', flat=True))

    try:
        current_index = ordered_ids.index(song.id)
    except ValueError:
        current_index = -1

    prev_song_id = ordered_ids[current_index - 1] if current_index > 0 else None
    next_song_id = ordered_ids[current_index + 1] if current_index < len(ordered_ids) - 1 else None

    context = {
        'song': song,
        'prev_song_id': prev_song_id,
        'next_song_id': next_song_id,
    }
    return render(request, 'music/play.html', context)

# ---------- استریم صوتی با پشتیبانی Range (Seek) ----------
def stream_audio(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    file_path = song.file_path
    if not os.path.exists(file_path):
        return HttpResponse(status=404)

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)')
    size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'

    if range_header:
        matches = range_re.match(range_header)
        if matches:
            start_byte = int(matches.group(1))
            end_byte = matches.group(2)
            end_byte = int(end_byte) if end_byte else size - 1
            if start_byte >= size:
                return HttpResponse(status=416)
            length = end_byte - start_byte + 1
            resp = StreamingHttpResponse(
                file_iterator(file_path, start_byte, end_byte),
                status=206,
                content_type=content_type
            )
            resp['Content-Range'] = f'bytes {start_byte}-{end_byte}/{size}'
            resp['Content-Length'] = str(length)
            resp['Accept-Ranges'] = 'bytes'
            return resp

    # بدون Range (کل فایل)
    resp = StreamingHttpResponse(file_iterator(file_path), content_type=content_type)
    resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp

def file_iterator(file_path, start=0, end=None):
    with open(file_path, 'rb') as f:
        f.seek(start)
        remaining = (end - start + 1) if end else None
        while True:
            chunk_size = 8192 if remaining is None else min(8192, remaining)
            data = f.read(chunk_size)
            if not data:
                break
            if remaining:
                remaining -= len(data)
            yield data
            if remaining is not None and remaining <= 0:
                break

# ---------- جستجوی AJAX (Auto Suggestion) ----------
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    # جستجوی سریع با ایندکس (LIKE)
    songs = Song.objects.filter(title__icontains=query)[:8]
    results = [{'id': s.id, 'title': s.title, 'artist': s.artist} for s in songs]
    return JsonResponse(results, safe=False)

# ---------- درباره ما ----------
def about(request):
    return render(request, 'music/about.html')

# ---------- احراز هویت (اختیاری) ----------
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'music/register.html', {'form': form})