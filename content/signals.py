import os
import django_rq
import shutil
from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from content.models import Video
from content.tasks import (
    convert_to_hls, 
    delete_origin_video_file,
    generate_thumbnail
)


@receiver (post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Convert a video file into HLS format using multiple quality profiles.
    Generates segmented playlists (m3u8 + ts files) for adaptive streaming.
    Stores the output under MEDIA_ROOT/videos/<video_id>/<resolution>/.
    """
    if not instance.video_file:
        return

    source = instance.video_file.path
    if not os.path.exists(source):
        return

    queue = django_rq.get_queue("default", autocommit=True)

    if not instance.thumbnail:
        queue.enqueue(
            generate_thumbnail,
            source,
            instance.id
        )

    if created:
        convert_job = queue.enqueue(
            convert_to_hls,
            source,
            instance.id
        )
        queue.enqueue(
            delete_origin_video_file,
            source,
            depends_on=convert_job
        )


@receiver(post_delete, sender=Video)       
def auto_delete_files_on_video_delete(sender, instance, **kwargs):
    """
    Triggered after a Video instance is deleted.
    
    - Deletes the associated original video file, if it exists.
    - Deletes the HLS directory for the video, if it exists.
    - Deletes the video thumbnail file, if it exists.
    """
    if instance.video_file and os.path.isfile(instance.video_file.path):
        os.remove(instance.video_file.path)

    hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(instance.id))
    if os.path.isdir(hls_dir):
        shutil.rmtree(hls_dir)

    if instance.thumbnail and os.path.isfile(instance.thumbnail.path):
        os.remove(instance.thumbnail.path)