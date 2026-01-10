"""
制約満足率調査スクリプト

初期状態（ランダム生成）の個体が制約を満たす割合を調査する。

Usage:
    cd backend
    python tests/test_constraint_satisfaction.py
"""

import os
import sys

# backendディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neat_core.population_manager import PopulationManager
from constraints.constraint_checker import ConstraintParams, ConstraintChecker


def run_test(num_trials: int = 100):
    """制約満足率テストを実行"""

    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'neat_config.txt'
    )
    config_path = os.path.abspath(config_path)

    params = ConstraintParams()
    checker = ConstraintChecker(params)

    # 統計カウンター
    total_genomes = 0
    pass_bounds = 0
    pass_h_speed = 0
    pass_v_speed = 0
    pass_distance = 0
    pass_all = 0

    print(f"\n=== Constraint Satisfaction Test ===")
    print(f"Parameters:")
    print(f"  Bounds: X[{params.x_min}, {params.x_max}], Y[{params.y_min}, {params.y_max}], Z[{params.z_min}, {params.z_max}]")
    print(f"  Max Speed: horizontal={params.max_horizontal_speed}m/s, vertical={params.max_vertical_speed}m/s")
    print(f"  Min Distance: {params.min_distance}m")
    print(f"\nRunning {num_trials} trials...")

    for trial in range(num_trials):
        # 新しい集団を生成
        pm = PopulationManager(config_path, num_drones=50)
        genome_ids = pm.get_genome_ids()

        for genome_id in genome_ids:
            animation = pm.generate_pattern(genome_id, duration=3.0)
            if animation is None:
                continue

            result = checker.check_animation(animation)
            total_genomes += 1

            if result.bounds_violations == 0:
                pass_bounds += 1
            if result.horizontal_speed_violations == 0:
                pass_h_speed += 1
            if result.vertical_speed_violations == 0:
                pass_v_speed += 1
            if result.distance_violations == 0:
                pass_distance += 1
            if result.passes_all:
                pass_all += 1

        # 進捗表示
        if (trial + 1) % 10 == 0:
            print(f"  Progress: {trial + 1}/{num_trials} trials")

    # 結果出力
    print(f"\n=== Results ===")
    print(f"Trials: {num_trials}")
    print(f"Genomes per trial: 12")
    print(f"Total genomes tested: {total_genomes}")
    print()
    print(f"  Pass bounds:    {pass_bounds}/{total_genomes} ({100*pass_bounds/total_genomes:.1f}%)")
    print(f"  Pass h-speed:   {pass_h_speed}/{total_genomes} ({100*pass_h_speed/total_genomes:.1f}%)")
    print(f"  Pass v-speed:   {pass_v_speed}/{total_genomes} ({100*pass_v_speed/total_genomes:.1f}%)")
    print(f"  Pass distance:  {pass_distance}/{total_genomes} ({100*pass_distance/total_genomes:.1f}%)")
    print(f"  Pass ALL:       {pass_all}/{total_genomes} ({100*pass_all/total_genomes:.1f}%)")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="制約満足率テスト")
    parser.add_argument("--trials", type=int, default=100, help="試行回数（デフォルト: 100）")
    args = parser.parse_args()

    run_test(num_trials=args.trials)
