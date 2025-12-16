"""
Evolution Test Script

PopulationManagerと進化ループの動作を確認します：
1. 集団を初期化
2. 各世代でパターンを生成
3. 自動適応度を計算（移動の多様性に基づく）
4. 次世代に進化
5. 最良パターンをJSON出力
"""

import os
import json
import math
from neat_core.population_manager import PopulationManager
from models.animation import Animation


def calculate_movement_diversity(animation: Animation) -> float:
    """
    アニメーションの移動多様性を計算

    各ドローンが移動した総距離を計算し、正規化します。
    これは自動適応度評価のための指標です。

    Args:
        animation: アニメーション

    Returns:
        float: 移動多様性スコア（0.0〜1.0）
    """
    if len(animation.frames) < 2:
        return 0.0

    total_distance = 0.0
    num_drones = len(animation.frames[0].drones)

    # 各ドローンの移動距離を計算
    for drone_idx in range(num_drones):
        for frame_idx in range(len(animation.frames) - 1):
            # 現在のフレームと次のフレーム
            current = animation.frames[frame_idx].drones[drone_idx]
            next_frame = animation.frames[frame_idx + 1].drones[drone_idx]

            # 2点間の距離
            dx = next_frame.x - current.x
            dy = next_frame.y - current.y
            dz = next_frame.z - current.z
            distance = math.sqrt(dx**2 + dy**2 + dz**2)

            total_distance += distance

    # 正規化（経験的な最大値で割る）
    # 5機のドローンが3秒間、最大速度2.0m/sで移動すると仮定
    max_possible_distance = num_drones * 3.0 * 2.0  # 30メートル
    normalized = min(total_distance / max_possible_distance, 1.0)

    return normalized


def calculate_color_variance(animation: Animation) -> float:
    """
    色の変化の多様性を計算

    フレーム間でRGB値がどれだけ変化するかを計算します。

    Args:
        animation: アニメーション

    Returns:
        float: 色変化スコア（0.0〜1.0）
    """
    if len(animation.frames) < 2:
        return 0.0

    total_color_change = 0.0
    num_drones = len(animation.frames[0].drones)

    # 各ドローンの色変化を計算
    for drone_idx in range(num_drones):
        for frame_idx in range(len(animation.frames) - 1):
            current = animation.frames[frame_idx].drones[drone_idx]
            next_frame = animation.frames[frame_idx + 1].drones[drone_idx]

            # RGB差分の絶対値
            dr = abs(next_frame.r - current.r)
            dg = abs(next_frame.g - current.g)
            db = abs(next_frame.b - current.b)
            color_change = (dr + dg + db) / 3.0  # 平均

            total_color_change += color_change

    # 正規化（最大RGB変化は255）
    num_transitions = num_drones * (len(animation.frames) - 1)
    normalized = min(total_color_change / (num_transitions * 255.0), 1.0)

    return normalized


def calculate_fitness(animation: Animation) -> float:
    """
    アニメーションから適応度を自動計算

    移動多様性と色変化を組み合わせたスコアを返します。
    これはテスト用の自動評価です。実際のPicbreederでは
    ユーザーが視覚的に評価します。

    Args:
        animation: アニメーション

    Returns:
        float: 適応度（0.0〜1.0）
    """
    movement_score = calculate_movement_diversity(animation)
    color_score = calculate_color_variance(animation)

    # 移動を重視（70%）、色変化を30%で評価
    fitness = 0.7 * movement_score + 0.3 * color_score

    return fitness


def main():
    print("=" * 60)
    print("Evolution Test - ドローンPicbreeder")
    print("=" * 60)
    print()

    # Step 1: 設定ファイルのパス
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, '..', 'config', 'neat_config.txt')
    config_path = os.path.abspath(config_path)

    print(f"📁 設定ファイル: {config_path}")

    # Step 2: PopulationManagerを初期化
    print("\n" + "-" * 60)
    print("Step 1: PopulationManagerを初期化")
    print("-" * 60)

    try:
        pm = PopulationManager(config_path, num_drones=5)
        print(f"✅ PopulationManagerを作成しました")
        print(f"   集団サイズ: {pm.get_population_size()}")
        print(f"   現在の世代: {pm.get_generation()}")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return

    # 出力ディレクトリ
    output_dir = os.path.join(local_dir, '..', 'output', 'evolution')
    os.makedirs(output_dir, exist_ok=True)

    # Step 3: 進化ループ
    num_generations = 3
    duration = 3.0  # 3秒のアニメーション

    print("\n" + "-" * 60)
    print(f"Step 2: {num_generations}世代の進化を実行")
    print("-" * 60)

    for gen in range(num_generations):
        print(f"\n🧬 世代 {pm.get_generation()}:")

        # 全ゲノムIDを取得
        genome_ids = pm.get_genome_ids()
        print(f"   ゲノム数: {len(genome_ids)}")

        # 各ゲノムのパターンを生成し、適応度を計算
        fitness_scores = {}
        animations = {}

        for genome_id in genome_ids:
            # アニメーションを生成
            animation = pm.generate_pattern(genome_id, duration)

            if animation is None:
                print(f"   ⚠️  ゲノム{genome_id}のパターン生成に失敗")
                continue

            # 適応度を計算
            fitness = calculate_fitness(animation)
            fitness_scores[genome_id] = fitness
            animations[genome_id] = animation

        # 適応度を割り当て
        pm.assign_fitness_batch(fitness_scores)

        # 適応度の統計を表示
        if fitness_scores:
            avg_fitness = sum(fitness_scores.values()) / len(fitness_scores)
            max_fitness = max(fitness_scores.values())
            min_fitness = min(fitness_scores.values())

            print(f"   適応度 - 平均: {avg_fitness:.4f}, 最大: {max_fitness:.4f}, 最小: {min_fitness:.4f}")

            # 最良のゲノムを取得
            best_genome = pm.get_best_genome()
            if best_genome:
                print(f"   最良ゲノム: ID={best_genome.key}, 適応度={best_genome.fitness:.4f}")

                # 最良パターンをJSON出力
                best_animation = animations[best_genome.key]
                output_path = os.path.join(output_dir, f"gen{pm.get_generation()}_best.json")

                with open(output_path, 'w', encoding='utf-8') as f:
                    animation_dict = best_animation.model_dump(exclude_none=True)
                    json.dump(animation_dict, f, indent=2, ensure_ascii=False)

                file_size = os.path.getsize(output_path)
                print(f"   ✅ 最良パターンを保存: {output_path} ({file_size / 1024:.1f} KB)")

        # 次世代に進化（最後の世代では進化しない）
        if gen < num_generations - 1:
            print(f"   🔄 次世代に進化中...")
            pm.evolve(default_fitness=0.0)

    # Step 4: まとめ
    print("\n" + "=" * 60)
    print("進化テスト完了！")
    print("=" * 60)
    print(f"\n最終世代: {pm.get_generation()}")
    print(f"集団サイズ: {pm.get_population_size()}")
    print(f"\n生成されたファイル:")

    for gen in range(num_generations):
        output_path = os.path.join(output_dir, f"gen{gen}_best.json")
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"  - {output_path} ({file_size / 1024:.1f} KB)")

    print("\n次のステップ:")
    print("1. JSONファイルをフロントエンドで可視化:")
    print(f"   cp {os.path.join(output_dir, 'gen*_best.json')} ../frontend/mock_data/")
    print("2. 各世代のパターンの進化を確認")
    print()


if __name__ == "__main__":
    main()
