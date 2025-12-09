from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    サーバーの動作確認用
    """
    return {
        "status": "ok",
        "message": "Drone Picbreeder API is running"
    }
