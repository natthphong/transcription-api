from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get(
    "/healthz",
    summary="Health Check",
    description="Return a minimal liveness payload for probes, containers, and gateway checks.",
)
def healthz():
    return {"ok": True}
