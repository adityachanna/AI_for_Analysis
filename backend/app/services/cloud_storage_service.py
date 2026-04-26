from pathlib import Path

from ..config import settings


def upload_to_bucket(source: Path, destination: str, content_type: str = "video/mp4") -> dict:
    if not settings.use_gcs:
        return {
            "uri": f"local://{source.as_posix()}",
            "bucket": "local",
            "object": destination,
            "provider": "local-filesystem",
        }

    try:
        from google.cloud import storage

        client = storage.Client(project=settings.google_cloud_project)
        bucket = client.bucket(settings.firebase_storage_bucket)
        blob = bucket.blob(destination)
        blob.upload_from_filename(str(source), content_type=content_type)
        return {
            "uri": f"gs://{settings.firebase_storage_bucket}/{destination}",
            "bucket": settings.firebase_storage_bucket,
            "object": destination,
            "provider": "gcs",
        }
    except Exception as exc:
        return {
            "uri": f"local://{source.as_posix()}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
            "error": str(exc),
        }
