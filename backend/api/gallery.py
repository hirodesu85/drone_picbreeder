from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db

router = APIRouter(prefix="/api/gallery")


class SaveAnimationRequest(BaseModel):
    animation_data: dict
    cppn_data: dict


class SaveAnimationResponse(BaseModel):
    id: int
    message: str


class AnimationListItem(BaseModel):
    id: int
    created_at: str


class AnimationListResponse(BaseModel):
    animations: list[AnimationListItem]
    total: int


class AnimationDetailResponse(BaseModel):
    id: int
    animation_data: dict
    cppn_data: dict
    created_at: str


class DeleteResponse(BaseModel):
    success: bool
    message: str


@router.post("/animations", response_model=SaveAnimationResponse)
async def save_animation(request: SaveAnimationRequest):
    """
    Save an animation to the gallery.
    """
    try:
        animation_id = db.save_animation(request.animation_data, request.cppn_data)
        return SaveAnimationResponse(
            id=animation_id,
            message="Animation saved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/animations", response_model=AnimationListResponse)
async def get_animations(offset: int = 0, limit: int = 50):
    """
    Get a list of saved animations (id and created_at only).
    """
    try:
        animations = db.get_animations_list(offset=offset, limit=limit)
        return AnimationListResponse(
            animations=animations,
            total=len(animations)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/animations/{animation_id}", response_model=AnimationDetailResponse)
async def get_animation(animation_id: int):
    """
    Get a single animation by ID.
    """
    try:
        animation = db.get_animation(animation_id)
        if animation is None:
            raise HTTPException(status_code=404, detail="Animation not found")
        return AnimationDetailResponse(**animation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/animations/{animation_id}", response_model=DeleteResponse)
async def delete_animation(animation_id: int):
    """
    Delete an animation by ID.
    """
    try:
        deleted = db.delete_animation(animation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Animation not found")
        return DeleteResponse(
            success=True,
            message="Animation deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
