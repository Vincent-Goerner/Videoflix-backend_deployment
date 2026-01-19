import os
from django.http import FileResponse, HttpResponse, Http404
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from content.models import Video
from content.api.serializers import VideoListSerializer
from content.api.permissions import CookieJWTAuthentication


class VideoListView(APIView):
    """
    API view to list all videos for authenticated users.
    Requires JWT cookie authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        """
        Retrieve all Video instances, serialize them, 
        and return as a JSON response with status 200.
        """
        videos = Video.objects.all()
        serializer = VideoListSerializer(
            videos,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class BaseHLSVideoView(APIView):
    """
    Base view for serving HLS video files securely.
    Handles video lookup and file path resolution.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get_video_or_404(self, movie_id: int) -> Video:
        """
        Retrieve a Video by ID, or raise Http404 if not found.
        """
        try:
            return Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

    def build_video_path(self, movie_id: int, resolution: str, filename: str) -> str:
        """
        Construct the absolute path to a video file.
        Raises Http404 if the file does not exist.
        """
        path = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            str(movie_id),
            resolution,
            filename,
        )
        if not os.path.exists(path):
            raise Http404("File not found")
        return path
    

class VideoPlaylistView(BaseHLSVideoView):
    """
    Serve HLS playlist files (.m3u8) for a given video and resolution.
    Inherits authentication and file lookup from BaseHLSVideoView.
    """
    def get(self, request, movie_id: int, resolution: str) -> HttpResponse:
        """
        Retrieve and return the HLS playlist file for the requested video.
        Raises Http404 if the video or file is not found or cannot be read.
        """
        self.get_video_or_404(movie_id)

        manifest_path = self.build_video_path(
            movie_id=movie_id,
            resolution=resolution,
            filename="index.m3u8",
        )

        try:
            with open(manifest_path, "r", encoding="utf-8") as file:
                return HttpResponse(
                    file.read(),
                    content_type="application/vnd.apple.mpegurl",
                    status=status.HTTP_200_OK,
                )
        except OSError:
            raise Http404("Error reading manifest file")
        

class HLSVideoSegmentView(BaseHLSVideoView):
    """
    Serve individual HLS video segments (.ts) for authenticated users.
    Inherits authentication and file lookup from BaseHLSVideoView.
    """
    def get(self, request, movie_id: int, resolution: str, segment: str) -> FileResponse:
        """
        Retrieve and return a specific video segment for HLS streaming.
        Raises Http404 if the video or segment file is not found or cannot be read.
        """
        self.get_video_or_404(movie_id)

        segment_path = self.build_video_path(
            movie_id=movie_id,
            resolution=resolution,
            filename=segment,
        )

        try:
            return FileResponse(
                open(segment_path, "rb"),
                content_type="video/MP2T",
                status=status.HTTP_200_OK,
            )
        except OSError:
            raise Http404("Error reading segment file")