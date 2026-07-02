# circuit-poster-tools

回路設計でよく使う早見表を、印刷用ポスターPDFとして生成するPythonスクリプト集です。各ツールは独立したディレクトリになっており、それぞれ単体で動作します。

## ツール一覧

| ディレクトリ | 内容 | 用紙サイズ |
|---|---|---|
| [resistor-poster](resistor-poster/) | 抵抗値系列（E12 / E24 / E48）早見表＋カラーコード表 | A0〜A4横 |
| [divider-poster](divider-poster/) | 2直列抵抗の分圧比（1%〜50%、E12/E24/E48）早見表 | A2横 / A4横 |
| [e6-divider-poster](e6-divider-poster/) | 2直列抵抗の分圧比（1%〜50%、E6のみで作れる値を全数掲載）早見表 | A2横 |
| [opamp-poster](opamp-poster/) | オペアンプ増幅回路のゲイン設定抵抗値早見表 | A2横 / A4横 |

それぞれの詳しい使い方・オプション・データ形式は各ディレクトリの README を参照してください。

## 共通の必要環境

- Python 3
- [reportlab](https://pypi.org/project/reportlab/)（各ディレクトリの `requirements.txt` からインストール可能）
- 日本語 TrueType フォント（IPAゴシック等。`.ttc` / `.otf` は非対応）

```bash
cd <ツールのディレクトリ>
pip install -r requirements.txt
python <スクリプト名>.py
```

生成されるPDFは各ツールのディレクトリ直下に出力されます（`.gitignore` によりGit管理対象外）。

## 生成PDFの配布（GitHub Releases）

生成物のPDF自体はGit管理せず、[GitHub Actions](.github/workflows/build-posters.yml) でビルドして Releases に添付する運用にしています。

- `v*.*.*` 形式のタグをpushすると、そのタグ名でReleaseを作成しPDFを添付（例: `git tag v1.0.0 && git push origin v1.0.0`）
- Actionsタブから手動実行（workflow_dispatch）すると、`latest` タグのプレリリースとしてPDFを最新化

いずれの場合もビルドはワークフロー実行のたびにゼロから行われるため、リポジトリ内のスクリプト・データの内容と生成PDFが常に一致します。

## ライセンス

このリポジトリ全体を [CC0 1.0 Universal](LICENSE) の下でパブリックドメインに提供します。著作権を主張せず、商用・非商用を問わず自由に複製・改変・再配布して構いません。
