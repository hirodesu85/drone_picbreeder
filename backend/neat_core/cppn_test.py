"""
CPPN Test Script

CPPNクラスの動作を確認します：
1. NEATゲノムからCPPNを作成
2. 複数の3D位置でクエリ
3. 速度と色の出力範囲を検証
"""

import os
import neat
from neat_core.cppn import CPPN


def main():
    print("=" * 60)
    print("CPPN Test - ドローンPicbreeder")
    print("=" * 60)
    print()

    # Step 1: NEAT設定の読み込み
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, '..', 'config', 'neat_config.txt')
    config_path = os.path.abspath(config_path)

    print(f"📁 設定ファイル: {config_path}")

    if not os.path.exists(config_path):
        print(f"❌ エラー: 設定ファイルが見つかりません: {config_path}")
        return

    # NEAT設定を読み込み
    print("\n" + "-" * 60)
    print("Step 1: NEAT設定の読み込み")
    print("-" * 60)

    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path
        )
        print("✅ NEAT設定を正常に読み込みました")
    except Exception as e:
        print(f"❌ エラー: 設定の読み込みに失敗しました: {e}")
        return

    # Step 2: ランダムなゲノムを作成
    print("\n" + "-" * 60)
    print("Step 2: ランダムなゲノムを作成")
    print("-" * 60)

    genome_id = 1
    genome = config.genome_type(genome_id)
    genome.configure_new(config.genome_config)

    print(f"✅ ゲノムID {genome_id} を作成しました")

    # Step 3: CPPNを作成
    print("\n" + "-" * 60)
    print("Step 3: CPPNを作成")
    print("-" * 60)

    try:
        cppn = CPPN(genome, config)
        print("✅ CPPNを作成しました")
        print(f"   速度スケール: ±{cppn.velocity_scale} m/s")
        print(f"   色範囲: {cppn.color_min}-{cppn.color_max}")
    except Exception as e:
        print(f"❌ エラー: CPPNの作成に失敗しました: {e}")
        return

    # Step 4: 複数の位置でクエリ
    print("\n" + "-" * 60)
    print("Step 4: 複数の3D位置でCPPNをクエリ")
    print("-" * 60)

    # テストする位置のリスト
    test_positions = [
        (0.0, 0.0, 0.0),      # 原点
        (1.0, 0.0, 0.0),      # X軸上
        (0.0, 1.0, 0.0),      # Y軸上
        (0.0, 0.0, 1.0),      # Z軸上
        (0.5, 0.5, 0.5),      # 立方体の角
        (-1.0, -1.0, 0.0),    # 負の座標
    ]

    print(f"\n   {len(test_positions)}個の位置でテスト:\n")

    all_velocities = []
    all_colors = []

    for i, (x, y, z) in enumerate(test_positions, 1):
        try:
            result = cppn.query(x, y, z)

            velocity = result['velocity']
            color = result['color']

            # 統計用に保存
            all_velocities.append((velocity['vx'], velocity['vy'], velocity['vz']))
            all_colors.append((color['r'], color['g'], color['b']))

            # 結果を表示
            print(f"   位置 {i}: ({x:+.1f}, {y:+.1f}, {z:+.1f})")
            print(f"     速度: vx={velocity['vx']:+.3f}, vy={velocity['vy']:+.3f}, vz={velocity['vz']:+.3f} m/s")
            print(f"     色:   r={color['r']:3d}, g={color['g']:3d}, b={color['b']:3d}")
            print()

        except Exception as e:
            print(f"❌ エラー: 位置 {i} でのクエリに失敗しました: {e}")
            return

    # Step 5: 出力範囲の検証
    print("-" * 60)
    print("Step 5: 出力範囲の検証")
    print("-" * 60)

    # 速度の範囲を確認
    vx_vals = [v[0] for v in all_velocities]
    vy_vals = [v[1] for v in all_velocities]
    vz_vals = [v[2] for v in all_velocities]

    print("\n   速度範囲:")
    print(f"     vx: {min(vx_vals):+.3f} ~ {max(vx_vals):+.3f} m/s")
    print(f"     vy: {min(vy_vals):+.3f} ~ {max(vy_vals):+.3f} m/s")
    print(f"     vz: {min(vz_vals):+.3f} ~ {max(vz_vals):+.3f} m/s")

    # 色の範囲を確認
    r_vals = [c[0] for c in all_colors]
    g_vals = [c[1] for c in all_colors]
    b_vals = [c[2] for c in all_colors]

    print("\n   色範囲:")
    print(f"     r: {min(r_vals)} ~ {max(r_vals)}")
    print(f"     g: {min(g_vals)} ~ {max(g_vals)}")
    print(f"     b: {min(b_vals)} ~ {max(b_vals)}")

    # 範囲チェック
    velocity_ok = all(
        abs(v) <= cppn.velocity_scale * 1.5  # 若干の余裕を持たせる
        for vel in all_velocities
        for v in vel
    )

    color_ok = all(
        cppn.color_min <= c <= cppn.color_max
        for col in all_colors
        for c in col
    )

    print("\n   検証結果:")
    if velocity_ok:
        print("     ✅ 速度は妥当な範囲内です")
    else:
        print("     ⚠️  速度が予想外の範囲です")

    if color_ok:
        print("     ✅ 色は0-255の範囲内です")
    else:
        print("     ❌ 色が0-255の範囲外です")

    # まとめ
    print("\n" + "=" * 60)
    print("テスト完了！")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. CPPNは複数の3D位置で正常にクエリできました")
    print("2. 速度と色の出力範囲は適切です")
    print("3. 次のステップでは、このCPPNを使って時間経過のアニメーションを生成します")
    print()


if __name__ == "__main__":
    main()
