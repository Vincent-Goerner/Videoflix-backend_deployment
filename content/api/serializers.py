from rest_framework import serializers
from content.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serialize Video objects with standard fields and a fully qualified thumbnail URL.
    """
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category',
            'video_file',
        ]

    def get_thumbnail_url(self, obj):
        """
        Return absolute URL of the thumbnail if it exists, otherwise None.
        """
        if not obj.thumbnail:
            return None

        url = getattr(obj.thumbnail, 'url', None)
        if not url:
            return None

        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url