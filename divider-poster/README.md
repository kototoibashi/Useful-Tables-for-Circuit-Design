# divider-poster

2直列抵抗（R1-R2）による分圧比の早見表を、印刷用A2横ポスターPDFとして生成するPythonスクリプトです。

## 特徴

- 分圧比 1%〜48%（0.25%刻み）を1枚の表にまとめて表示
- 各セルには実際に使用する抵抗値の組み合わせ（R1-R2）を表示
- 枠線の色で使用系列（E12 / E24 / E48）を判別
  - E12・E24：枠線のみ
  - E48：枠線＋下線
  - 該当なし（±0.125%以内に組み合わせが存在しない）：斜線
- 49%〜50%の範囲は表に収まらないため、フッターに補足リストとして表示

## 必要環境

- Python 3
- [reportlab](https://pypi.org/project/reportlab/)
- 日本語 TrueType フォント（IPAゴシック）

```bash
pip install -r requirements.txt
```

### フォントについて

このスクリプトはフォントパスを `/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf` に**固定**で参照します（コマンドラインオプションでの変更には対応していません）。

```bash
# Ubuntu / Debian の例
sudo apt-get install fonts-ipafont-gothic
```

別環境・別フォントを使う場合は、`make_poster_final.py` 冒頭の `pdfmetrics.registerFont(...)` の行を直接書き換えてください。

## 使い方

このディレクトリ内で実行してください（データファイルを相対パスで読み込むため）。

```bash
cd divider-poster
python make_poster_final.py
```

`voltage_divider_poster_final.pdf`（A2横向き）がこのディレクトリ内に生成されます。出力先やページサイズを変えるコマンドラインオプションはありません。

## データファイル

スクリプトは同ディレクトリ内の2つのJSONを読み込みます。値を変更したい場合はこれらを直接編集してください。

- `table_data_grid_1_48.json` — 分圧比 1%〜48% の本表データ。
  ```json
  {
    "<整数部（%）>": [
      {"target": 1.0, "src": "E12", "ratio": 0.99, "r1": 2200, "r2": 22, "ok": true},
      ...  // +0.0% / +0.25% / +0.5% / +0.75% の4要素
    ]
  }
  ```
  - `src`: 使用した抵抗系列（`E12` / `E24` / `E48`）
  - `ratio`: 実際の分圧比（%）
  - `r1`, `r2`: 抵抗値（そのまま Ω として使用可能な整数表記）
  - `ok`: `false` の場合は許容誤差内に組み合わせが存在しない（表では斜線表示）
- `list_49_50_grouped.json` — 49%〜50% 用の補足リスト（フッター表示のみ、同じフィールド構成）

## 数値の読み方

`Vout = Vin × R2/(R1+R2)` となるよう、表に記載の `R1-R2` の値をそのまま抵抗値（Ω・kΩなど任意の桁）として使用してください。

## ライセンス

このリポジトリ全体のライセンスに従います。ルートの [LICENSE](../LICENSE)（CC0 1.0 Universal）を参照してください。
