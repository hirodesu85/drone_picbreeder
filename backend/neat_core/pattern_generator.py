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
        self.fps = 30  # フレームレート（30fps）
        self.dt = 1.0 / self.fps  # タイムステップ（秒）

        # 初期配置パラメータ
        self.initial_radius = 1.5  # 正多角形の半径（メートル）
        self.initial_z = 0.0  # 初期Z座標（地上）

    def generate_initial_positions(self) -> List[Tuple[float, float, float]]:
        """
        ドローンの初期位置を生成

        正多角形（XY平面、z=0）の配置を生成します。

        Returns:
            List[Tuple[float, float, float]]: (x, y, z)のタプルのリスト
        """
        positions = []
        angle_step = 2.0 * math.pi / self.num_drones

        for i in range(self.num_drones):
            # 正多角形の頂点を計算（最初のドローンはX軸正方向）
            angle = i * angle_step
            x = self.initial_radius * math.cos(angle)
            y = self.initial_radius * math.sin(angle)
            z = self.initial_z

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
