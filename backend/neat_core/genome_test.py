"""
NEAT Genome Test Script

このスクリプトはNEATの基本動作を確認します：
1. 設定ファイルの読み込み
2. ランダムなゲノムの作成
3. ゲノムからニューラルネットワークの構築
4. ネットワークへの入力と出力の確認
"""

import os
import math
import neat


def main():
    print("=" * 60)
    print("NEAT Genome Test - ドローンPicbreeder")
    print("=" * 60)
    print()

    # Step 1: 設定ファイルのパスを取得
    # このスクリプトの場所から相対パスで設定ファイルを探す
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, '..', 'config', 'neat_config.txt')
    config_path = os.path.abspath(config_path)

    print(f"📁 設定ファイル: {config_path}")

    # 設定ファイルの存在確認
    if not os.path.exists(config_path):
        print(f"❌ エラー: 設定ファイルが見つかりません: {config_path}")
        return

    # Step 2: NEAT設定の読み込み
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
        print(f"   入力数: {config.genome_config.num_inputs}")
        print(f"   出力数: {config.genome_config.num_outputs}")
        print(f"   集団サイズ: {config.pop_size}") # type: ignore[attr-defined]
        print(f"   活性化関数: {', '.join(config.genome_config.activation_options)}")
    except Exception as e:
        print(f"❌ エラー: 設定の読み込みに失敗しました: {e}")
        return

    # Step 3: ランダムなゲノムの作成
    print("\n" + "-" * 60)
    print("Step 2: ランダムなゲノムの作成")
    print("-" * 60)

    # ゲノムIDは任意の整数（ここでは1を使用）
    genome_id = 1
    genome = config.genome_type(genome_id)

    # configure_newメソッドでランダムに初期化
    genome.configure_new(config.genome_config)

    print(f"✅ ゲノムID {genome_id} を作成しました")
    print(f"   ノード数: {len(genome.nodes)}")
    print(f"   接続数: {len(genome.connections)}")

    # ゲノムの構造を表示
    print("\n   ゲノム構造:")

    # 入力ノードの表示（設定から取得）
    print(f"   - 入力ノード: {config.genome_config.num_inputs}個 (設定による)")

    # 出力ノードの表示
    output_nodes = [n for n in genome.nodes.keys() if n >= 0 and n < config.genome_config.num_outputs]
    print(f"   - 出力ノード: {len(output_nodes)}個 (ID: {output_nodes})")

    # 隠れノードの表示
    hidden_nodes = [n for n in genome.nodes.keys() if n >= config.genome_config.num_outputs]
    print(f"   - 隠れノード: {len(hidden_nodes)}個")

    # Step 4: ニューラルネットワークの構築
    print("\n" + "-" * 60)
    print("Step 3: ニューラルネットワークの構築")
    print("-" * 60)

    try:
        # ゲノムから実際に動作するニューラルネットワークを作成
        network = neat.nn.FeedForwardNetwork.create(genome, config)
        print("✅ フィードフォワードネットワークを構築しました")
    except Exception as e:
        print(f"❌ エラー: ネットワークの構築に失敗しました: {e}")
        return

    # Step 5: ネットワークのテスト
    print("\n" + "-" * 60)
    print("Step 4: ネットワークのテスト")
    print("-" * 60)

    # テスト入力: ドローンの位置 (x=0.5, y=0.5, z=0.5)
    # 原点からの距離 d = √(0.5² + 0.5² + 0.5²) ≈ 0.866
    x, y, z = 0.5, 0.5, 0.5
    d = math.sqrt(x**2 + y**2 + z**2)

    print(f"\n   テスト入力:")
    print(f"   - ドローン位置: (x={x}, y={y}, z={z})")
    print(f"   - 原点からの距離: d={d:.3f}")
    print(f"   - 入力ベクトル: [{x}, {y}, {z}, {d:.3f}]")

    # ネットワークに入力を与えて出力を取得
    try:
        output = network.activate([x, y, z, d])

        print(f"\n   ネットワーク出力 (6個の値):")
        print(f"   - 生の出力: {[f'{v:.3f}' for v in output]}")

        # 出力の解釈
        vx, vy, vz = output[0:3]
        r, g, b = output[3:6]

        print(f"\n   出力の解釈:")
        print(f"   - 速度ベクトル: (vx={vx:.3f}, vy={vy:.3f}, vz={vz:.3f})")
        print(f"   - 色成分 (未スケール): (r={r:.3f}, g={g:.3f}, b={b:.3f})")

        print("\n   ✅ ネットワークは正常に動作しています！")

    except Exception as e:
        print(f"❌ エラー: ネットワークの実行に失敗しました: {e}")
        return

    # まとめ
    print("\n" + "=" * 60)
    print("テスト完了！")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. このゲノムはランダムに初期化されたので、出力も一応ランダムです")
    print("2. 次のステップでは、この出力を適切にスケール（調整）します")
    print("3. その後、進化によってより興味深いパターンを生成します")
    print()


if __name__ == "__main__":
    main()
