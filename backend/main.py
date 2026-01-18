from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import routes
from api import evolution
from api import gallery

app = FastAPI(
    title="Drone Picbreeder API",
    description="NEAT/CPPNを用いたドローンショーのパターン生成API",
    version="0.1.0"
)

# CORS設定（開発環境用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では specific origins を指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(routes.router)
app.include_router(evolution.router)
app.include_router(gallery.router)
