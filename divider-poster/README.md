# divider-poster

2直列抵抗（R1-R2）による分圧比の早見表を、印刷用ポスターPDF（A2・A4）およびMarkdown表として生成するPythonスクリプトです。

## 特徴

- 分圧比 1%〜48%（0.25%刻み）を1枚の表にまとめて表示
- 各セルには実際に使用する抵抗値の組み合わせ（R1-R2）を表示
- 枠線の色で使用系列（E12 / E24 / E48）を判別
  - E12・E24：枠線のみ
  - E48：枠線＋下線
  - 該当なし（±0.125%以内に組み合わせが存在しない）：斜線
- 49%〜50%の範囲は表に収まらないため、フッターに補足リストとして表示
- A2版とA4版でレイアウトを個別最適化（デフォルトで両方生成）
- `--markdown` 指定でGitHub等にそのまま貼れるMarkdown表も出力可能

## 必要環境

- Python 3
- [reportlab](https://pypi.org/project/reportlab/)
- 日本語 TrueType フォント（IPAゴシック、またはWindowsのMS ゴシック/メイリオ）

```bash
pip install -r requirements.txt
```

### フォントについて

スクリプトは以下の候補を順に探し、最初に見つかったものを使用します。

1. `/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf`（Linux）
2. `C:/Windows/Fonts/msgothic.ttc`（Windows）
3. `C:/Windows/Fonts/meiryo.ttc`（Windows）

```bash
# Ubuntu / Debian の例
sudo apt-get install fonts-ipafont-gothic
```

いずれも見つからない場合はエラーで終了します。別のフォントを使いたい場合は `make_poster_final.py` 冒頭の `font_paths` リストを直接書き換えてください（コマンドラインオプションでの指定には対応していません）。

## 使い方

このディレクトリ内で実行してください（データファイルを相対パスで読み込むため）。

```bash
cd divider-poster

# デフォルト: A2・A4の両方のPDFを生成
python make_poster_final.py

# A2のみ / A4のみ生成
python make_poster_final.py --size A2
python make_poster_final.py --size A4

# PDFを生成せず、Markdown表だけ出力
python make_poster_final.py --size none --markdown
```

`voltage_divider_poster_A2.pdf` / `voltage_divider_poster_A4.pdf` がこのディレクトリ内に生成されます。`--markdown`（`-m`）を付けると `voltage_divider_table.md` も併せて出力されます。

### オプション一覧

| オプション | 説明 | デフォルト |
|---|---|---|
| `--size` | 生成するPDFサイズ（`A2` / `A4` / `both` / `none`） | `both` |
| `-m`, `--markdown` | Markdown表（`voltage_divider_table.md`）も生成する | 指定なし |

## 50%を超える比率が必要な場合

この表は1%〜50%の範囲しか掲載していませんが、`Vout = Vin × R2/(R1+R2)` という式の性質上、目標比率が x%（x > 50）のときは (100-x)% の行を探し、その R1 と R2 を入れ替えれば厳密に x% が得られます（`R1/(R1+R2) = 1 - R2/(R1+R2)` という恒等式のため、近似ではなく正確に成立します）。

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
