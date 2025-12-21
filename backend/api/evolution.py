"""
Evolution API Endpoints

NEAT進化のためのAPIエンドポイント。
Step 5でセッション管理を実装。
"""

import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional
from neat_core.population_manager import PopulationManager
from models.animation import Animation
from api.session_manager import get_session_manager


# ルーターを作成
router = APIRouter(prefix="/api/evolution", tags=["evolution"])


# リクエスト/レスポンスモデル
class InitializeRequest(BaseModel):
    """進化初期化リクエスト"""
    num_drones: int = Field(default=5, ge=1, le=100, description="ドローンの数")


class InitializeResponse(BaseModel):
    """進化初期化レスポンス"""
    session_id: str
    message: str
    population_size: int
    generation: int


class GenomesResponse(BaseModel):
    """ゲノムIDリストレスポンス"""
    genome_ids: List[int]
    generation: int
    population_size: int


class FitnessRequest(BaseModel):
    """適応度割り当てリクエスト"""
    genome_id: int = Field(..., description="ゲノムID")
    fitness: float = Field(..., ge=0.0, le=1.0, description="適応度（0.0〜1.0）")


class FitnessResponse(BaseModel):
    """適応度割り当てレスポンス"""
    success: bool
    message: str


class EvolveRequest(BaseModel):
    """進化リクエスト"""
    default_fitness: float = Field(default=0.0, ge=0.0, le=1.0,
                                   description="未割り当てゲノムのデフォルト適応度")


class EvolveResponse(BaseModel):
    """進化レスポンス"""
    success: bool
    message: str
    new_generation: int
    population_size: int


class StatusResponse(BaseModel):
    """ステータスレスポンス"""
    initialized: bool
    generation: Optional[int] = None
    population_size: Optional[int] = None
    fitness_status: Optional[dict] = None


# エンドポイント実装

@router.post("/initialize", response_model=InitializeResponse)
async def initialize(request: InitializeRequest):
    """
    新しい進化セッションを初期化し、セッションIDを発行
    """
    # 設定ファイルのパス
    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'neat_config.txt'
    )
    config_path = os.path.abspath(config_path)

    try:
        session_manager = get_session_manager()
        session_id = session_manager.create_session(
            config_path,
            num_drones=request.num_drones
        )

        population_manager = session_manager.get_session(session_id)

        return InitializeResponse(
            session_id=session_id,
            message="進化セッションを初期化しました",
            population_size=population_manager.get_population_size(),
            generation=population_manager.get_generation()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初期化エラー: {str(e)}")


@router.get("/genomes", response_model=GenomesResponse)
async def get_genomes(x_session_id: str = Header(None, alias="X-Session-ID")):
    """
    現在の世代の全ゲノムIDを取得
    """
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="セッションIDが指定されていません。X-Session-IDヘッダーを設定してください。"
        )

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        raise HTTPException(
            status_code=404,
            detail="セッションが見つかりません。/api/evolution/initializeで新しいセッションを開始してください。"
        )

    genome_ids = population_manager.get_genome_ids()

    return GenomesResponse(
        genome_ids=genome_ids,
        generation=population_manager.get_generation(),
        population_size=population_manager.get_population_size()
    )


@router.get("/pattern/{genome_id}", response_model=Animation)
async def get_pattern(
    genome_id: int,
    duration: float = 3.0,
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    特定のゲノムからアニメーションパターンを生成

    Args:
        genome_id: ゲノムID
        duration: アニメーションの長さ（秒）
    """
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="セッションIDが指定されていません。X-Session-IDヘッダーを設定してください。"
        )

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        raise HTTPException(
            status_code=404,
            detail="セッションが見つかりません。/api/evolution/initializeで新しいセッションを開始してください。"
        )

    animation = population_manager.generate_pattern(genome_id, duration)

    if animation is None:
        raise HTTPException(status_code=404, detail=f"ゲノムID {genome_id} が見つかりません")

    return animation


@router.post("/fitness", response_model=FitnessResponse)
async def assign_fitness(
    request: FitnessRequest,
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    ゲノムに適応度を割り当て
    """
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="セッションIDが指定されていません。X-Session-IDヘッダーを設定してください。"
        )

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        raise HTTPException(
            status_code=404,
            detail="セッションが見つかりません。/api/evolution/initializeで新しいセッションを開始してください。"
        )

    success = population_manager.assign_fitness(request.genome_id, request.fitness)

    if not success:
        raise HTTPException(status_code=404, detail=f"ゲノムID {request.genome_id} が見つかりません")

    return FitnessResponse(
        success=True,
        message=f"ゲノム {request.genome_id} に適応度 {request.fitness:.4f} を割り当てました"
    )


@router.post("/evolve", response_model=EvolveResponse)
async def evolve(
    request: EvolveRequest,
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    次世代に進化
    """
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="セッションIDが指定されていません。X-Session-IDヘッダーを設定してください。"
        )

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        raise HTTPException(
            status_code=404,
            detail="セッションが見つかりません。/api/evolution/initializeで新しいセッションを開始してください。"
        )

    try:
        success = population_manager.evolve(default_fitness=request.default_fitness)

        return EvolveResponse(
            success=success,
            message="次世代に進化しました",
            new_generation=population_manager.get_generation(),
            population_size=population_manager.get_population_size()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"進化エラー: {str(e)}")


@router.get("/status", response_model=StatusResponse)
async def get_status(x_session_id: str = Header(None, alias="X-Session-ID")):
    """
    進化セッションのステータスを取得

    セッションIDが指定されていない場合は、セッションが未初期化として扱います。
    """
    if not x_session_id:
        return StatusResponse(initialized=False)

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        return StatusResponse(initialized=False)

    return StatusResponse(
        initialized=True,
        generation=population_manager.get_generation(),
        population_size=population_manager.get_population_size(),
        fitness_status=population_manager.get_fitness_status()
    )
