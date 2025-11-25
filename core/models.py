from django.db import models
from django.utils import timezone


class Recording(models.Model):
    """
    Store metadata about Agora Cloud Recordings

    This model tracks all recordings with meaningful information like
    channel name, timestamps, duration, and S3 file locations.
    """

    # Agora Recording identifiers
    resource_id = models.CharField(max_length=255, unique=True)
    sid = models.CharField(max_length=255, unique=True)

    # Recording details
    channel_name = models.CharField(max_length=255, db_index=True)
    recording_uid = models.CharField(max_length=50, default="999999")

    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    stopped_at = models.DateTimeField(null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('recording', 'Recording'),
        ('stopped', 'Stopped'),
        ('uploaded', 'Uploaded'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recording')

    # S3 Storage info
    s3_bucket = models.CharField(max_length=255, blank=True)
    s3_file_list = models.TextField(blank=True, help_text="JSON list of recording files")

    # Additional metadata
    mode = models.CharField(max_length=20, default='mix', help_text="Recording mode: mix or individual")

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['channel_name', '-started_at']),
        ]

    def __str__(self):
        return f"{self.channel_name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def duration_seconds(self):
        """Calculate recording duration in seconds"""
        if self.stopped_at:
            return int((self.stopped_at - self.started_at).total_seconds())
        return 0

    @property
    def duration_formatted(self):
        """Return formatted duration (HH:MM:SS)"""
        if not self.stopped_at:
            return "Recording..."

        seconds = self.duration_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @property
    def is_active(self):
        """Check if recording is currently active"""
        return self.status == 'recording'
