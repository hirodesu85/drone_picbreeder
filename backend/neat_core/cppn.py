"""
CPPN (Compositional Pattern Producing Networks) Wrapper

このモジュールはNEATゲノムをドローンパターン生成用のCPPNとしてラップします。
CPPNは3D座標を入力として、その位置でのドローンの速度と色を出力します。
"""

import math
import neat


class CPPN:
    """
    CPPNラッパークラス

    NEATゲノムから作成されたニューラルネットワークを、
    ドローンパターン生成用のCPPNとして扱うためのクラス。

    入力: (x, y, z) - ドローンの3D座標
    出力: 速度ベクトル (vx, vy, vz) と色 (r, g, b)
    """

    def __init__(self, genome, config):
        """
        CPPNを初期化

        Args:
            genome: NEATゲノム
            config: NEAT設定オブジェクト
        """
        self.genome = genome
        self.config = config
        # ゲノムからフィードフォワードネットワークを作成
        self.network = neat.nn.FeedForwardNetwork.create(genome, config)

        # 出力スケーリングパラメータ
        # 速度: 生の出力（通常 -1~1 の範囲）を ±2.0 m/s にスケール
        self.velocity_scale = 2.0
        # 色: 生の出力を 0-255 の RGB 範囲にマッピング
        self.color_min = 0
        self.color_max = 255

    def query(self, x: float, y: float, z: float) -> dict:
        """
        指定された3D座標でCPPNにクエリ

        Args:
            x: X座標 (メートル)
            y: Y座標 (メートル)
            z: Z座標 (メートル)

        Returns:
            dict: 以下のキーを持つ辞書
                - 'velocity': {'vx': float, 'vy': float, 'vz': float} (m/s)
                - 'color': {'r': int, 'g': int, 'b': int} (0-255)
        """
        # 原点からの距離を計算（放射対称パターン用）
        d = math.sqrt(x**2 + y**2 + z**2)

        # ネットワークを活性化: 4入力 → 6出力
        raw_output = self.network.activate([x, y, z, d])

        # 出力を解釈
        # 最初の3つ: 速度成分
        vx_raw, vy_raw, vz_raw = raw_output[0:3]
        # 次の3つ: 色成分
        r_raw, g_raw, b_raw = raw_output[3:6]

        # 速度をスケーリング
        # NEATの活性化関数（sigmoid, tanh等）の出力範囲に依存
        # ここでは単純にvelocity_scaleを掛ける
        velocity = {
            'vx': vx_raw * self.velocity_scale,
            'vy': vy_raw * self.velocity_scale,
            'vz': vz_raw * self.velocity_scale
        }

        # 色を0-255の範囲にマッピング
        # 生の出力（通常-1~1または0~1）を[0, 255]にスケール
        # sigmoid出力の場合: 0~1 → 0~255
        # tanh出力の場合: -1~1 → 0~255
        color = {
            'r': self._scale_to_color(r_raw),
            'g': self._scale_to_color(g_raw),
            'b': self._scale_to_color(b_raw)
        }

        return {
            'velocity': velocity,
            'color': color
        }

    def _scale_to_color(self, raw_value: float) -> int:
        """
        生のネットワーク出力を0-255のRGB値にスケール

        Args:
            raw_value: ネットワークの生の出力値

        Returns:
            int: 0-255の範囲にクリップされた整数値
        """
        # 生の値を[-1, 1]または[0, 1]の範囲と仮定
        # まず[0, 1]の範囲にマッピング
        # tanh等の[-1, 1]出力の場合: (raw + 1) / 2
        # sigmoid等の[0, 1]出力の場合: そのまま
        # 安全のため、[-1, 1]を想定して変換
        normalized = (raw_value + 1.0) / 2.0

        # [0, 255]にスケール
        scaled = normalized * (self.color_max - self.color_min) + self.color_min

        # 0-255の範囲にクリップして整数に
        clipped = max(self.color_min, min(self.color_max, scaled))

        return int(clipped)
