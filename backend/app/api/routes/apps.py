from fastapi import APIRouter, HTTPException, status

from app.platform.apps import AppManifest, get_app_registry

router = APIRouter(tags=["Applications"])


@router.get("/apps", response_model=list[AppManifest])
def list_applications() -> list[AppManifest]:
    return get_app_registry().list_enabled()


@router.get("/apps/{app_id}", response_model=AppManifest)
def get_application(app_id: str) -> AppManifest:
    manifest = get_app_registry().get(app_id)
    if manifest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return manifest
