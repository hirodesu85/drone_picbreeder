"""
Animation Data Models

ドローンアニメーションのためのPydanticモデル。
フロントエンドが期待するJSON形式に対応しています。
"""

from typing import List
from pydantic import BaseModel, Field


class DroneState(BaseModel):
    """
    単一のドローンの状態（位置と色）

    CPPNが生成した位置と色の情報を含みます。
    フロントエンドはこれらの値を使用して3Dビジュアライゼーションを行います。
    """
    x: float = Field(..., description="X座標 (メートル)")
    y: float = Field(..., description="Y座標 (メートル)")
    z: float = Field(..., description="Z座標 (メートル)")
    # 色情報（CPPNが生成、フロントエンドで表示に使用）
    r: int = Field(default=127, ge=0, le=255, description="赤成分 (0-255)")
    g: int = Field(default=255, ge=0, le=255, description="緑成分 (0-255)")  # デフォルトは蛍光グリーン
    b: int = Field(default=127, ge=0, le=255, description="青成分 (0-255)")


class Frame(BaseModel):
    """
    アニメーションの1フレーム

    特定の時刻における全ドローンの状態を表します。
    """
    t: float = Field(..., description="時刻 (秒)", ge=0.0)
    drones: List[DroneState] = Field(..., description="ドローンの状態リスト")

    class Config:
        json_schema_extra = {
            "example": {
                "t": 0.0,
                "drones": [
                    {"x": 1.5, "y": 0.0, "z": 0.0, "r": 127, "g": 255, "b": 127},
                    {"x": 0.464, "y": 1.427, "z": 0.0, "r": 127, "g": 255, "b": 127}
                ]
            }
        }


class Animation(BaseModel):
    """
    完全なドローンアニメーション

    ゲノムIDと時系列フレームを含みます。
    """
    id: int = Field(..., description="ゲノムID")
    frames: List[Frame] = Field(..., description="アニメーションフレームのリスト")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 0,
                "frames": [
                    {
                        "t": 0.0,
                        "drones": [
                            {"x": 1.5, "y": 0.0, "z": 0.0, "r": 127, "g": 255, "b": 127}
                        ]
                    }
                ]
            }
        }
