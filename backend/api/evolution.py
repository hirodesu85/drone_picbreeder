"""
Evolution API Endpoints

NEAT進化のためのAPIエンドポイント。
Step 5でセッション管理を実装。
"""

import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from neat_core.population_manager import PopulationManager
from models.animation import Animation
from api.session_manager import get_session_manager
from constraints.constraint_checker import ConstraintParams, check_all_genomes


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


class CPPNNode(BaseModel):
    """CPPNノード情報"""
    id: int
    type: str  # "input", "output", "hidden"
    label: str
    activation: str
    bias: float


class CPPNConnection(BaseModel):
    """CPPNコネクション情報"""
    from_node: int = Field(..., alias="from")
    to_node: int = Field(..., alias="to")
    weight: float
    enabled: bool

    class Config:
        populate_by_name = True


class CPPNStructure(BaseModel):
    """CPPN network structure information"""
    genome_id: int
    nodes: List[CPPNNode]
    connections: List[CPPNConnection]

    class Config:
        populate_by_name = True


class GenomeHistoryItem(BaseModel):
    """個別ゲノムの履歴情報"""
    genome_id: int
    parent1: Optional[int] = None
    parent2: Optional[int] = None
    fitness: Optional[float] = None


class GenerationHistory(BaseModel):
    """世代ごとの履歴情報"""
    generation: int
    genomes: List[GenomeHistoryItem]


class EvolutionHistoryResponse(BaseModel):
    """進化履歴レスポンス"""
    history: List[GenerationHistory]
    total_generations: int


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


@router.get("/cppn/{genome_id}", response_model=CPPNStructure)
async def get_cppn_structure(
    genome_id: int,
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    特定のゲノムのCPPN構造を取得

    Args:
        genome_id: ゲノムID
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
            detail="セッションが見つかりません。"
        )

    genome = population_manager.get_genome(genome_id)

    if genome is None:
        raise HTTPException(
            status_code=404,
            detail=f"ゲノムID {genome_id} が見つかりません"
        )

    # Extract CPPN structure
    config = population_manager.config
    num_inputs = config.genome_config.num_inputs
    num_outputs = config.genome_config.num_outputs

    # Input node IDs are negative
    input_ids = list(range(-num_inputs, 0))
    output_ids = list(range(num_outputs))
    hidden_ids = [nid for nid in genome.nodes.keys() if nid >= num_outputs]

    # Build node list
    nodes = []

    # Input nodes
    input_labels = ["x", "y", "z", "d"]
    for i, nid in enumerate(input_ids):
        nodes.append(CPPNNode(
            id=nid,
            type="input",
            label=input_labels[i] if i < len(input_labels) else f"input_{i}",
            activation="identity",
            bias=0.0
        ))

    # Output nodes
    output_labels = ["vx", "vy", "vz", "r", "g", "b"]
    for i, nid in enumerate(output_ids):
        node = genome.nodes.get(nid)
        if node:
            nodes.append(CPPNNode(
                id=nid,
                type="output",
                label=output_labels[i] if i < len(output_labels) else f"output_{i}",
                activation=node.activation,
                bias=node.bias
            ))

    # Hidden nodes
    for nid in hidden_ids:
        node = genome.nodes[nid]
        nodes.append(CPPNNode(
            id=nid,
            type="hidden",
            label=f"h{nid}",
            activation=node.activation,
            bias=node.bias
        ))

    # Build connection list
    connections = []
    for conn_key, conn in genome.connections.items():
        connections.append(CPPNConnection(
            **{
                "from": conn_key[0],
                "to": conn_key[1],
                "weight": conn.weight,
                "enabled": conn.enabled
            }
        ))

    return CPPNStructure(
        genome_id=genome_id,
        nodes=nodes,
        connections=connections
    )


@router.get("/history", response_model=EvolutionHistoryResponse)
async def get_evolution_history(
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    進化履歴を取得

    全世代のゲノム情報（ID、親情報、適応度）を返します。
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
            detail="セッションが見つかりません。"
        )

    history = population_manager.get_evolution_history()

    return EvolutionHistoryResponse(
        history=history,
        total_generations=len(history)
    )


class ConstraintCheckResponse(BaseModel):
    """制約チェックレスポンス"""
    success: bool
    message: str


@router.post("/constraints/check", response_model=ConstraintCheckResponse)
async def check_constraints(
    x_session_id: str = Header(None, alias="X-Session-ID")
):
    """
    全12個体の制約違反をチェックし、コンソールにログ出力
    """
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="セッションIDが指定されていません。"
        )

    session_manager = get_session_manager()
    population_manager = session_manager.get_session(x_session_id)

    if population_manager is None:
        raise HTTPException(
            status_code=404,
            detail="セッションが見つかりません。"
        )

    # 全ゲノムのアニメーションを生成
    genome_ids = population_manager.get_genome_ids()
    animations = []
    for genome_id in genome_ids:
        animation = population_manager.generate_pattern(genome_id, duration=3.0)
        if animation:
            animations.append(animation)

    # 制約チェック
    params = ConstraintParams()
    check_result = check_all_genomes(animations, params)

    # コンソール出力
    print("\n" + "=" * 60)
    print("CONSTRAINT CHECK RESULTS")
    print("=" * 60)
    print(f"Parameters:")
    print(f"  Bounds: X[{params.x_min}, {params.x_max}], Y[{params.y_min}, {params.y_max}], Z[{params.z_min}, {params.z_max}]")
    print(f"  Max Speed: horizontal={params.max_horizontal_speed}m/s, vertical={params.max_vertical_speed}m/s")
    print(f"  Min Distance: {params.min_distance}m")
    print("-" * 60)

    for result in check_result["results"]:
        status = "PASS" if result.passes_all else "FAIL"
        print(f"\nGenome {result.genome_id}: {status}")
        print(f"  Bounds:     {result.bounds_violations} violations (max: {result.max_bounds_violation:.3f}m)")
        print(f"  H-Speed:    {result.horizontal_speed_violations} violations")
        print(f"  V-Speed:    {result.vertical_speed_violations} violations")
        min_dist = result.min_distance_observed if result.min_distance_observed != float('inf') else 0
        print(f"  Distance:   {result.distance_violations} violations (min: {min_dist:.3f}m)")

    summary = check_result["summary"]
    print("\n" + "-" * 60)
    print("SUMMARY")
    print(f"  Pass bounds:    {summary['pass_bounds']}/{summary['total']}")
    print(f"  Pass h-speed:   {summary['pass_h_speed']}/{summary['total']}")
    print(f"  Pass v-speed:   {summary['pass_v_speed']}/{summary['total']}")
    print(f"  Pass distance:  {summary['pass_distance']}/{summary['total']}")
    print(f"  Pass ALL:       {summary['pass_all']}/{summary['total']}")
    print("=" * 60 + "\n")

    return ConstraintCheckResponse(
        success=True,
        message=f"制約チェック完了: {summary['pass_all']}/{summary['total']} 個体が全制約をパス"
    )
