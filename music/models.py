from django.db import models

class Song(models.Model):
    title = models.CharField(max_length=200, db_index=True)   # ایندکس برای سرچ سریع
    artist = models.CharField(max_length=200, blank=True, default='Unknown')
    album = models.CharField(max_length=200, blank=True, default='Unknown')
    duration = models.PositiveIntegerField(help_text='Duration in seconds')
    file_path = models.CharField(max_length=500, unique=True) # مسیر کامل فایل
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title', 'artist']),   # ایندکس ترکیبی برای جستجو
        ]

    def __str__(self):
        return f"{self.artist} - {self.title}"