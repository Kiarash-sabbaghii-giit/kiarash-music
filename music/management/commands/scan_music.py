import os
from pathlib import Path
from django.core.management.base import BaseCommand
from music.models import Song
from mutagen import File as MutagenFile
from concurrent.futures import ThreadPoolExecutor, as_completed

# مسیر ریشه‌ی پروژه (جایی که manage.py هست)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MUSIC_FOLDER = str(BASE_DIR / 'musics')

def process_file(filepath):
    try:
        audio = MutagenFile(filepath)
        if audio is None:
            return None
        length = int(audio.info.length)
        title = str(audio.get('title', [os.path.basename(filepath)])[0])
        artist = str(audio.get('artist', ['Unknown'])[0])
        album = str(audio.get('album', ['Unknown'])[0])
        return Song(
            title=title,
            artist=artist,
            album=album,
            duration=length,
            file_path=os.path.abspath(filepath),
        )
    except Exception as e:
        # چاپ خطا برای شفافیت، اما ادامه می‌دهیم
        print(f"Skipping {filepath}: {e}")
        return None

class Command(BaseCommand):
    help = 'Scan music folder and populate database'

    def handle(self, *args, **options):
        if not os.path.exists(MUSIC_FOLDER):
            self.stdout.write(self.style.ERROR(f'Folder not found: {MUSIC_FOLDER}'))
            return

        # جمع‌آوری همه فایل‌های صوتی
        music_files = []
        for root, dirs, files in os.walk(MUSIC_FOLDER):
            for f in files:
                if f.lower().endswith(('.mp3', '.flac', '.wav', '.ogg', '.m4a')):
                    music_files.append(os.path.join(root, f))

        self.stdout.write(f'Found {len(music_files)} files. Processing...')

        # 🧵 پردازش چندنخی برای سرعت
        songs_to_create = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_file, f): f for f in music_files}
            for future in as_completed(futures):
                song = future.result()
                if song:
                    songs_to_create.append(song)

        if not songs_to_create:
            self.stdout.write('No valid music files found.')
            return

        # جلوگیری از ورود داده تکراری بدون ignore_conflicts
        # ۱. مسیرهای موجود در دیتابیس را یکجا می‌خوانیم
        existing_paths = set(Song.objects.values_list('file_path', flat=True))
        # ۲. فقط آهنگ‌هایی که file_path آن‌ها جدید است نگه می‌داریم
        new_songs = [s for s in songs_to_create if s.file_path not in existing_paths]

        if new_songs:
            Song.objects.bulk_create(new_songs)   # بدون ignore_conflicts
            self.stdout.write(self.style.SUCCESS(f'Added {len(new_songs)} new songs.'))
        else:
            self.stdout.write('No new songs to add (all already in DB).')