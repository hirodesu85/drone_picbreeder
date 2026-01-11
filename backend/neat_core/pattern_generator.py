"""
Pattern Generator

CPPNからドローンアニメーションを生成します。
速度出力をオイラー法で時間積分し、フレームごとの位置と色を計算します。
"""

import math
from typing import List, Tuple
from neat_core.cppn import CPPN
from models.animation import Animation, Frame, DroneState


class PatternGenerator:
    """
    CPPNからドローンアニメーションを生成するクラス

    時間積分により、CPPNの速度出力から飛行経路を生成します。
    """

    def __init__(self, cppn: CPPN, genome_id: int, num_drones: int = 5):
        """
        PatternGeneratorを初期化

        Args:
            cppn: パターン生成に使用するCPPN
            genome_id: ゲノムID（アニメーションのIDとして使用）
            num_drones: ドローンの数（デフォルト: 5）
        """
        self.cppn = cppn
        self.genome_id = genome_id
        self.num_drones = num_drones

        # シミュレーションパラメータ
        self.fps = 25  # フレームレート（25fps）
        self.dt = 1.0 / self.fps  # タイムステップ（秒）

        # 3Dグリッド配置パラメータ
        self.grid_x = 5  # X方向の数
        self.grid_y = 5  # Y方向の数
        self.grid_z = 2  # Z方向の数（層数）
        self.grid_spacing = 1.0  # グリッドの間隔（メートル）

        # パラメータ検証
        expected_drones = self.grid_x * self.grid_y * self.grid_z
        if self.num_drones != expected_drones:
            raise ValueError(
                f"num_drones ({self.num_drones}) must match grid size "
                f"({self.grid_x}x{self.grid_y}x{self.grid_z}={expected_drones})"
            )

    def generate_initial_positions(self) -> List[Tuple[float, float, float]]:
        """
        ドローンの初期位置を生成（5x5x2の3Dグリッド配置）

        グリッドの中心を原点(0, 0, 0)に配置します。

        Returns:
            List[Tuple[float, float, float]]: (x, y, z)のタプルのリスト
        """
        positions = []

        # グリッドの中心オフセットを計算
        x_offset = -(self.grid_x - 1) * self.grid_spacing / 2.0
        y_offset = -(self.grid_y - 1) * self.grid_spacing / 2.0
        z_offset = -(self.grid_z - 1) * self.grid_spacing / 2.0

        # 3Dグリッドでドローンを配置（Z層 → Y行 → X列 の順）
        for i in range(self.num_drones):
            z_idx = i // (self.grid_x * self.grid_y)
            remainder = i % (self.grid_x * self.grid_y)
            y_idx = remainder // self.grid_x
            x_idx = remainder % self.grid_x

            x = x_idx * self.grid_spacing + x_offset
            y = y_idx * self.grid_spacing + y_offset
            z = z_idx * self.grid_spacing + z_offset

            positions.append((x, y, z))

        return positions

    def generate_animation(self, duration: float = 3.0) -> Animation:
        """
        CPPNから完全なアニメーションを生成

        Args:
            duration: アニメーションの長さ（秒）

        Returns:
            Animation: 生成されたアニメーション
        """
        # フレーム数を計算
        num_frames = int(duration * self.fps) + 1  # +1は最後のフレームを含む

        # 初期位置
        positions = self.generate_initial_positions()

        frames = []

        for frame_idx in range(num_frames):
            # 現在の時刻
            t = frame_idx * self.dt

            # 各ドローンの状態を計算
            drone_states = []

            for drone_idx in range(self.num_drones):
                x, y, z = positions[drone_idx]

                # CPPNにクエリして速度と色を取得
                result = self.cppn.query(x, y, z)
                velocity = result['velocity']
                color = result['color']

                # DroneStateを作成
                drone_state = DroneState(
                    x=x,
                    y=y,
                    z=z,
                    r=color['r'],
                    g=color['g'],
                    b=color['b']
                )

                drone_states.append(drone_state)

                # 次のフレームのために位置を更新（オイラー法）
                # position_new = position_old + velocity × dt
                if frame_idx < num_frames - 1:  # 最後のフレームでは更新しない
                    new_x = x + velocity['vx'] * self.dt
                    new_y = y + velocity['vy'] * self.dt
                    new_z = z + velocity['vz'] * self.dt
                    positions[drone_idx] = (new_x, new_y, new_z)

            # フレームを作成
            frame = Frame(t=t, drones=drone_states)
            frames.append(frame)

        # アニメーションを作成
        animation = Animation(id=self.genome_id, frames=frames)

        return animation
