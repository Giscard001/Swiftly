from fastapi import APIRouter

from ..capabilities import capabilities_payload

router = APIRouter()


@router.get("/capabilities")
def get_capabilities():
    return capabilities_payload()
