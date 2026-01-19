from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import Video


User = get_user_model()

class VideoListViewTest(APITestCase):
    """
    Test suite for VideoListView to ensure proper listing of videos.
    Covers authenticated and unauthenticated access scenarios.
    """
    def setUp(self):
        """
        Prepare test environment: create a test user, a sample video,
        and authenticate the test client.
        """
        self.user = User.objects.create_user(
            username="testuser",
            password="secret"
        )

        self.video = Video.objects.create(
            title="Test Video"
        )

        self.client.force_authenticate(user=self.user)

    def test_get_video_list_authenticated(self):
        """
        Test that an authenticated user can retrieve the list of videos.
        Checks response status 200 and that the returned video matches the test video.
        """
        url = reverse("video-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.video.id)

    def test_get_video_list_unauthenticated(self):
        """
        Test that an unauthenticated user cannot access the video list.
        Expects response status 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)

        url = reverse("video-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)