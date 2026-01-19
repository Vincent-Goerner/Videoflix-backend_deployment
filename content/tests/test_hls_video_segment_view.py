import os
import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import Video


User = get_user_model()

class HLSVideoSegmentViewTest(APITestCase):
    """
    Test suite for HLSVideoSegmentView to ensure proper streaming of video segments.
    Includes setup of temporary media, authenticated user, and sample video.
    """
    def setUp(self):
        """
        Prepare test environment: temporary MEDIA_ROOT, create test user and video,
        and authenticate the test client.
        """
        self._temp_media = tempfile.mkdtemp()
        self._old_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self._temp_media

        self.user = User.objects.create_user(
            username="testuser",
            password="secret"
        )

        self.video = Video.objects.create(
            title="Test Video"
        )

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """
        Clean up temporary media and restore original MEDIA_ROOT.
        """
        settings.MEDIA_ROOT = self._old_media_root
        shutil.rmtree(self._temp_media)

    def _create_segment(self, resolution="720p", segment="segment1.ts"):
        """
        Helper method to create a fake HLS video segment file for testing.
        """
        base_path = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            str(self.video.id),
            resolution,
        )
        os.makedirs(base_path, exist_ok=True)

        segment_path = os.path.join(base_path, segment)
        with open(segment_path, "wb") as f:
            f.write(b"fake ts data")

    def test_get_segment_success(self):
        """
        Test that an existing video segment is returned successfully with 200 status
        and correct 'video/MP2T' content type.
        """
        self._create_segment()

        url = reverse(
            "video-segment",
            kwargs={
                "movie_id": self.video.id,
                "resolution": "720p",
                "segment": "segment1.ts",
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/MP2T")

    def test_get_segment_not_found(self):
        """
        Test that requesting a non-existent segment returns 404 Not Found.
        """
        url = reverse(
            "video-segment",
            kwargs={
                "movie_id": self.video.id,
                "resolution": "720p",
                "segment": "does_not_exist.ts",
            },
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_segment_video_not_found(self):
        """
        Test that requesting a segment for a non-existent video returns 404 Not Found.
        """
        url = reverse(
            "video-segment",
            kwargs={
                "movie_id": 9999,
                "resolution": "720p",
                "segment": "segment1.ts",
            },
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)