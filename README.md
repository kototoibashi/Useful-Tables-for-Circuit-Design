# circuit-poster-tools

回路設計でよく使う早見表を、印刷用ポスターPDFとして生成するPythonスクリプト集です。各ツールは独立したディレクトリになっており、それぞれ単体で動作します。

## ツール一覧

| ディレクトリ | 内容 | 用紙サイズ |
|---|---|---|
| [resistor-poster](resistor-poster/) | 抵抗値系列（E12 / E24 / E48）早見表＋カラーコード表 | A0〜A4横 |
| [divider-poster](divider-poster/) | 2直列抵抗の分圧比（1%〜50%）早見表 | A2横 |
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

## ライセンス

このリポジトリ全体を [CC0 1.0 Universal](LICENSE) の下でパブリックドメインに提供します。著作権を主張せず、商用・非商用を問わず自由に複製・改変・再配布して構いません。
