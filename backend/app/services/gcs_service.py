import io
import logging
from pathlib import Path
from typing import BinaryIO

from google.cloud import storage
from google.cloud.storage.blob import Blob

from ..config import settings

logger = logging.getLogger(__name__)

_client = None


def get_gcs_client() -> storage.Client | None:
    """Get authenticated GCS client."""
    global _client
    if _client is not None:
        return _client

    if not settings.use_gcs:
        return None

    try:
        if settings.gcs_credentials:
            _client = storage.Client.from_service_account_json(settings.gcs_credentials)
        else:
            _client = storage.Client(project=settings.google_cloud_project)
        return _client
    except Exception as e:
        logger.warning(f"GCS client init failed: {e}. Using local fallback.")
        return None


def upload_to_gcs(source: Path | str, destination: str, content_type: str = "video/mp4") -> dict:
    """Upload file to Google Cloud Storage bucket."""
    if not settings.use_gcs:
        source_path = Path(source)
        return {
            "uri": f"local://{source_path.as_posix()}",
            "bucket": "local",
            "object": destination,
            "provider": "local-filesystem",
            "size_bytes": source_path.stat().st_size if source_path.exists() else 0,
        }

    client = get_gcs_client()
    if not client:
        source_path = Path(source)
        return {
            "uri": f"local://{source_path.as_posix()}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
        }

    try:
        bucket = client.bucket(settings.gcs_bucket_name)
        blob: Blob = bucket.blob(destination)

        if isinstance(source, str):
            blob.upload_from_filename(source, content_type=content_type)
        else:
            blob.upload_from_file(source, content_type=content_type)

        return {
            "uri": f"gs://{settings.gcs_bucket_name}/{destination}",
            "bucket": settings.gcs_bucket_name,
            "object": destination,
            "provider": "gcs",
            "size_bytes": blob.size,
            "created": blob.time_created.isoformat() if blob.time_created else datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        return {
            "uri": f"local://{Path(source).as_posix()}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
            "error": str(e),
        }


def upload_bytes_to_gcs(data: bytes, destination: str, content_type: str = "video/mp4") -> dict:
    """Upload byte data directly to GCS."""
    if not settings.use_gcs:
        return {
            "uri": f"local://memory/{destination}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
        }

    client = get_gcs_client()
    if not client:
        return {
            "uri": f"local://memory/{destination}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
        }

    try:
        bucket = client.bucket(settings.gcs_bucket_name)
        blob: Blob = bucket.blob(destination)
        blob.upload_from_file(io.BytesIO(data), content_type=content_type)
        return {
            "uri": f"gs://{settings.gcs_bucket_name}/{destination}",
            "bucket": settings.gcs_bucket_name,
            "object": destination,
            "provider": "gcs",
            "size_bytes": len(data),
        }
    except Exception as e:
        logger.error(f"GCS byte upload failed: {e}")
        return {
            "uri": f"local://memory/{destination}",
            "bucket": "local",
            "object": destination,
            "provider": "local-fallback",
            "error": str(e),
        }


def download_from_gcs(gcs_uri: str, destination: Path | None = None) -> dict:
    """Download file from GCS bucket."""
    if gcs_uri.startswith("local://"):
        local_path = Path(gcs_uri.replace("local://", ""))
        if destination and local_path.exists():
            import shutil
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(local_path, destination)
        return {"status": "downloaded", "path": str(destination or local_path)}

    if not gcs_uri.startswith("gs://"):
        return {"status": "error", "error": "Invalid GCS URI format"}

    client = get_gcs_client()
    if not client:
        return {"status": "error", "error": "GCS client unavailable"}

    try:
        uri_parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name, object_name = uri_parts[0], uri_parts[1]
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        if destination is None:
            destination = Path(settings.UPLOAD_DIR) / Path(object_name).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(destination))

        return {
            "status": "downloaded",
            "path": str(destination),
            "size_bytes": blob.size,
        }
    except Exception as e:
        logger.error(f"GCS download failed: {e}")
        return {"status": "error", "error": str(e)}


def list_bucket_contents(prefix: str = "", max_results: int = 100) -> list[dict]:
    """List objects in GCS bucket."""
    client = get_gcs_client()
    if not client:
        return []

    try:
        bucket = client.bucket(settings.gcs_bucket_name)
        blobs = bucket.list_blobs(prefix=prefix, max_results=max_results)
        return [
            {
                "name": blob.name,
                "size_bytes": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "uri": f"gs://{settings.gcs_bucket_name}/{blob.name}",
            }
            for blob in blobs
        ]
    except Exception as e:
        logger.error(f"GCS list failed: {e}")
        return []


def delete_from_gcs(object_name: str) -> dict:
    """Delete object from GCS bucket."""
    client = get_gcs_client()
    if not client:
        return {"status": "error", "error": "GCS client unavailable"}

    try:
        bucket = client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(object_name)
        blob.delete()
        return {"status": "deleted", "object": object_name}
    except Exception as e:
        logger.error(f"GCS delete failed: {e}")
        return {"status": "error", "error": str(e)}


from datetime import datetime