# -*- coding: utf-8 -*-
"""
2直列抵抗 分圧比 早見表のグリッドデータ(1〜48%, 0.25%刻み)を生成するスクリプト。

出力: table_data_grid_1_48.json
  { "1": [ {target, src, ratio, r1, r2, ok}, ... x4 (offset 0.0/0.25/0.5/0.75) ], "2": [...], ... "48": [...] }

アルゴリズム:
1. E12の組み合わせ(桁差 -2/-1/0)で各ターゲット(1.00, 1.25, 1.50, ... 49.75%)に最も近い比率を探す
2. 同じ組み合わせが複数のターゲットに割り当てられた場合、最もフィットしているターゲットだけ残し、
   それ以外のターゲットはE24で再検索する(E24でも重複するものはE48で再検索)
   ※この「最良フィットだけ残す」処理が無いと、たまたま完全一致している組み合わせまで
     格上げされて劣化するバグがあるため注意(過去に発生した実例: 40.0%ちょうどのケース)
3. 許容誤差 ±0.125% (= 0.25%刻みの半分) を超えるものは "ok": false としてマークする
   (ポスター上では斜線=該当なしとして表示する想定)
"""
import json

E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
E48 = [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
       1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
       3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
       5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53]

DECADES = [-2, -1, 0]          # R2の桁がR1の1/100, 1/10, 同じ桁
OFFSETS = [0.0, 0.25, 0.5, 0.75]  # 0.25%刻み
ROWS = list(range(1, 50))      # 1%〜49%（後で1〜48%だけ切り出す）
TOLERANCE = 0.125               # 許容誤差 ±0.125%


def build_pool(series, scale):
    """
    series の値どうしの組み合わせ(桁差 -2,-1,0)から、
    (比率, R1の整数表記, R2の整数表記) のリストを作る。

    表記ルール: R1_new = round(R1*scale) * 10^|d|, R2_new = round(R2*scale)
    こうすると R2_new/(R1_new+R2_new) が元の比率と一致する整数ペアになる。
    """
    pool = []
    for d in DECADES:
        for r1 in series:
            for r2 in series:
                r2_scaled = r2 * (10 ** d)
                ratio = r2_scaled / (r1 + r2_scaled) * 100
                if ratio <= 50.0:
                    r1_new = round(r1 * scale) * (10 ** abs(d))
                    r2_new = round(r2 * scale)
                    pool.append((ratio, r1_new, r2_new))
    return pool


def nearest(pool, target):
    return min(pool, key=lambda c: (abs(c[0] - target), min(c[1], c[2])))


def resolve(pool_seq_names, pools, targets):
    """
    E12 -> E24 -> E48 の順に、各ターゲットへ最も近い組み合わせを割り当てる。

    解決ルール:
    1. 重複解決: ある組み合わせが複数のターゲットに「最近傍」として選ばれた場合、
       その中で最もフィットしている(誤差が最小の)ターゲットだけその系列の結果を採用し、
       残りは次の系列で再検索する。
    2. 誤差解決: 割り当てられた結果の誤差が許容誤差(TOLERANCE)を超える場合、
       そのターゲットは次の系列で再検索する。
    """
    assign = {t: (pool_seq_names[0], *nearest(pools[pool_seq_names[0]], t)) for t in targets}

    for stage in range(len(pool_seq_names) - 1):
        cur_src = pool_seq_names[stage]
        next_src = pool_seq_names[stage + 1]

        groups = {}
        for t, (src, ratio, r1n, r2n) in assign.items():
            if src == cur_src:
                groups.setdefault((r1n, r2n), []).append(t)

        for combo, ts in groups.items():
            if len(ts) <= 1:
                continue
            ts_sorted = sorted(ts, key=lambda t: abs(assign[t][1] - t))
            best_t = ts_sorted[0]  # 最もフィットしているターゲットはそのまま残す
            for t in ts_sorted[1:]:
                ratio, r1n, r2n = nearest(pools[next_src], t)
                assign[t] = (next_src, ratio, r1n, r2n)

        # 許容誤差を超えているターゲットも次の系列にアップグレードする
        for t, (src, ratio, r1n, r2n) in list(assign.items()):
            if src == cur_src:
                if abs(ratio - t) > TOLERANCE:
                    ratio_next, r1n_next, r2n_next = nearest(pools[next_src], t)
                    assign[t] = (next_src, ratio_next, r1n_next, r2n_next)

    return assign


def main():
    pools = {
        'E24': build_pool(E24, 10),
        'E48': build_pool(E48, 100),
    }

    targets = [round(r + o, 2) for r in ROWS for o in OFFSETS]
    assign = resolve(['E24', 'E48'], pools, targets)

    # E12 の判定用値リスト
    E12_scaled = [round(x * 10) for x in E12]

    def is_e12_value(val):
        while val % 10 == 0 and val not in E12_scaled:
            val //= 10
        return val in E12_scaled

    data_full = {}
    for r in ROWS:
        row_data = []
        for o in OFFSETS:
            t = round(r + o, 2)
            src, ratio, r1n, r2n = assign[t]
            if src == 'E24' and is_e12_value(r1n) and is_e12_value(r2n):
                src = 'E12'
            ok = abs(ratio - t) <= TOLERANCE
            row_data.append({
                'target': t, 'src': src, 'ratio': round(ratio, 3),
                'r1': r1n, 'r2': r2n, 'ok': ok,
            })
        data_full[str(r)] = row_data

    na_count = sum(1 for row in data_full.values() for c in row if not c['ok'])
    total = len(targets)
    print(f"該当なし: {na_count}/{total} ({na_count/total*100:.1f}%)")

    # ポスターでは1〜48%だけをグリッド表として使う（49%以降は別枠でテキスト表記）
    grid_1_48 = {str(r): data_full[str(r)] for r in range(1, 49)}

    with open('table_data_grid_1_48.json', 'w', encoding='utf-8') as f:
        json.dump(grid_1_48, f, ensure_ascii=False)

    print(f"table_data_grid_1_48.json を書き出しました（{len(grid_1_48)}行）")


if __name__ == '__main__':
    main()
