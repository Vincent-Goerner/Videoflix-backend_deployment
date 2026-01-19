from django.db import models
from datetime import date
from django.core.exceptions import ValidationError

MOVIE_CATEGORY = [
    ('action', 'Action'),
    ('adventure', 'Adventure'),
    ('comedy', 'Comedy'),
    ('drama', 'Drama'),
    ('documentation', 'Documentation'),
    ('horror', 'Horror'),
    ('sci-fi', 'Sci-fi'),
    ('thriller', 'Thriller'),
    ('western', 'Western'),
    ('fantasy', 'Fantasy'),
    ('crime', 'Crime'),
    ('romance', 'Romance')
]

class Video(models.Model):
    created_at = models.DateField(default=date.today)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos')
    thumbnail = models.ImageField(upload_to='thumbnail/', blank=True, null=True)
    category = models.CharField(max_length=30, choices=MOVIE_CATEGORY, default='action')

    def __str__(self):
        return self.title
