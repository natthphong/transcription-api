from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from app.services.storage import get_object_stream

router = APIRouter(tags=["storage"])


@router.get("/file")
async def get_file(key: str = Query(..., min_length=1)):
    try:
        obj, content_type, size = get_object_stream(key)
    except S3Error as e:
        if e.code in {"NoSuchKey", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="file not found")
        raise HTTPException(status_code=500, detail=f"storage error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"storage error: {e}")

    def _iter():
        try:
            for chunk in obj.stream(32 * 1024):
                yield chunk
        finally:
            obj.close()
            obj.release_conn()

    headers = {}
    if size is not None:
        headers["Content-Length"] = str(size)
    return StreamingResponse(
        _iter(),
        media_type=content_type or "application/octet-stream",
        headers=headers,
    )
