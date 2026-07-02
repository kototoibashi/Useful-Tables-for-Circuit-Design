# opamp-poster

オペアンプ増幅回路（反転／非反転）のゲイン設定に使う抵抗値早見表を、印刷用ポスターPDFとして生成するPythonスクリプトです。入力抵抗 R1（Zin）を 39 / 51 / 100 / 200 Ω に固定し、目標ゲイン（1, 2, 3, 4, 5, 7.5, 10 倍）ごとに必要な R2 を一覧表示します。

2つのスクリプトがあり、用紙サイズと構成が異なります。

| スクリプト | 用紙サイズ | 特徴 |
|---|---|---|
| `make_opamp_poster.py` | A2横 | 抵抗値早見表のみ |
| `make_opamp_poster_a4.py` | A4横 | 早見表に加え、回路図画像を埋め込み可能（3カラムレイアウト） |

## 特徴

- 反転・非反転アンプそれぞれについて、R1×ゲインの表を作成
- 各セルには使用する抵抗系列（E12 / E24 / E48）に応じた枠線色と、E48利用時の下線を表示
- E24で近似できる代替値がある場合は `[E24代替]` として併記
- （A4版のみ）`opamp_circuit_uploaded.png` が存在すればポスター内に回路図として埋め込み、なければプレースホルダー枠を表示

## 必要環境

- Python 3
- [reportlab](https://pypi.org/project/reportlab/)
- 日本語 TrueType フォント（IPAゴシック）

```bash
pip install -r requirements.txt
```

### フォントについて

両スクリプトともフォントパスを `/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf` に**固定**で参照します（コマンドラインオプションでの変更には対応していません）。

```bash
# Ubuntu / Debian の例
sudo apt-get install fonts-ipafont-gothic
```

別環境・別フォントを使う場合は、各スクリプト冒頭の `pdfmetrics.registerFont(...)` の行を直接書き換えてください。

## 使い方

このディレクトリ内で実行してください（データファイルを相対パスで読み込むため）。

```bash
cd opamp-poster

# A2横ポスター（抵抗値早見表のみ）
python make_opamp_poster.py
# -> opamp_poster.pdf が生成される

# A4横ポスター（回路図付き）
python make_opamp_poster_a4.py
# -> opamp_poster_a4.pdf が生成される
```

出力先やページサイズを変えるコマンドラインオプションはありません。

### 回路図を埋め込む（A4版のみ）

`opamp_circuit_uploaded.png` という名前の画像をこのディレクトリに置いてから `make_opamp_poster_a4.py` を実行すると、ポスター左カラムに回路図として埋め込まれます（このファイルは `.gitignore` でGit管理対象外にしています）。

## データファイル

`opamp_data.json` に反転／非反転アンプそれぞれのゲイン早見データが入っています。値を変更したい場合は直接編集してください。

```json
{
  "inverting": {
    "<ゲイン>": {
      "<R1>": {"r2": 100.0, "src": "E12", "gain": 2.0, "alt24": {"r2": 200, "gain": 2.02}}
    }
  },
  "noninverting": { ... }
}
```

- `r2`: 目標ゲインに最も近い抵抗値
- `src`: 使用した抵抗系列（`E12` / `E24` / `E48`）
- `gain`: `r2` を使った場合の実際のゲイン
- `alt24`: （任意）E24系列で代替する場合の値とゲイン

## ライセンス

このリポジトリ全体のライセンスに従います。ルートの [LICENSE](../LICENSE)（CC0 1.0 Universal）を参照してください。
