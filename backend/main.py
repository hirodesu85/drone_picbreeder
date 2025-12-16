from fastapi import FastAPI
from api import routes
from api import evolution

app = FastAPI(
    title="Drone Picbreeder API",
    description="NEAT/CPPNを用いたドローンショーのパターン生成API",
    version="0.1.0"
)

# ルーターの登録
app.include_router(routes.router)
app.include_router(evolution.router)
