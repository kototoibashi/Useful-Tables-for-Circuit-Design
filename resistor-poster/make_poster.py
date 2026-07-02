#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抵抗値系列(E12 / E24 / E48)早見ポスター PDF ジェネレーター
===========================================================

E12・E24(E12との重複を除く)・E48 の抵抗値系列を1枚のA2横ポスターに
まとめ、補足として抵抗器カラーコード表も添えたPDFを生成します。

数値の表記について
-------------------
ポスターとして見やすくするため、小数点を排して整数表記にしています。
    - E12 / E24 : 元の値 x 10   (例: 2.2 -> 22)
    - E48       : 元の値 x 100  (例: 2.26 -> 226)
実際の抵抗値を得るには、表の数値を上記の逆数(E12/E24は1/10、E48は1/100)
倍してから、必要な10のべき乗(x0.1, x1, x10, x100, x1k, ...)を掛けてください。

使い方
------
    python make_poster.py
    python make_poster.py -o output/my_poster.pdf
    python make_poster.py --pagesize A1

依存パッケージ:
    pip install reportlab

日本語フォント:
    IPAゴシック相当のTrueTypeフォントが必要です。
    Ubuntu/Debian: sudo apt-get install fonts-ipafont-gothic
    のようにインストールしてください。
    (Noto Sans CJK など、CFFアウトラインのOpenType(.ttc/.otf)は
    reportlabのTTFontで直接扱えないため非対応です。TrueType(.ttf)を
    指定してください。 --font-path で明示的に指定することも可能です。)
"""

import argparse
import glob
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---------------------------------------------------------------------------
# データ定義
# ---------------------------------------------------------------------------

# (E12 x10, E24(E12重複を除く) x10, [E48 x100 の値のリスト])
# E48の各値は「同じ行のE12値以上、次の行のE12値未満」の範囲に含まれるものを
# 割り当てている。
RESISTOR_ROWS = [
    (10, 11, [100, 105, 110, 115]),
    (12, 13, [121, 127, 133, 140, 147]),
    (15, 16, [154, 162, 169]),
    (18, 20, [178, 187, 196, 205, 215]),
    (22, 24, [226, 237, 249, 261]),
    (27, 30, [274, 287, 301, 316]),
    (33, 36, [332, 348, 365, 383]),
    (39, 43, [402, 422, 442, 464]),
    (47, 51, [487, 511, 536]),
    (56, 62, [562, 590, 619, 649]),
    (68, 75, [681, 715, 750, 787]),
    (82, 91, [825, 866, 909, 953]),
]

# 抵抗器カラーコード (色名, 数字, 乗数, 許容差, 背景色hex, 白文字か)
COLOR_CODE_ROWS = [
    ("黒", "0", "×1", "-", "#000000", True),
    ("茶", "1", "×10", "±1%", "#7B3F00", True),
    ("赤", "2", "×100", "±2%", "#E30613", True),
    ("橙", "3", "×1,000", "-", "#F39200", False),
    ("黄", "4", "×10,000", "-", "#FFD500", False),
    ("緑", "5", "×100,000", "±0.5%", "#00843D", True),
    ("青", "6", "×1,000,000", "±0.25%", "#0057A0", True),
    ("紫", "7", "-", "±0.1%", "#5C2D91", True),
    ("灰", "8", "-", "-", "#8C8C8C", False),
    ("白", "9", "-", "-", "#FFFFFF", False),
    ("金", "-", "×0.1", "±5%", "#C8A030", False),
    ("銀", "-", "×0.01", "±10%", "#C0C0C0", False),
]

PAGE_SIZES = {
    "A0": A0,
    "A1": A1,
    "A2": A2,
    "A3": A3,
    "A4": A4,
}

# フォント探索候補 (TrueType の日本語フォントのみ。CFF系OpenTypeは非対応)
DEFAULT_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
    "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
]


def find_japanese_font(explicit_path=None):
    """日本語TrueTypeフォントのパスを返す。見つからなければNone。"""
    if explicit_path:
        if os.path.isfile(explicit_path):
            return explicit_path
        raise FileNotFoundError(f"指定されたフォントが見つかりません: {explicit_path}")

    for path in DEFAULT_FONT_CANDIDATES:
        if os.path.isfile(path):
            return path

    # 最後の手段として ttf ファイルを名前で検索する
    for pattern in ("*ipag*.ttf", "*japanese*.ttf", "*gothic*.ttf"):
        matches = glob.glob(f"/usr/share/fonts/**/{pattern}", recursive=True)
        if matches:
            return matches[0]

    return None


def cell(v):
    return "" if v is None else str(v)


def build_story(page_w, page_h, font_name, font_bold):
    """ポスター本体のFlowableリスト(story)を組み立てる。"""
    story = []

    title_style = ParagraphStyle(
        "title", fontName=font_bold, fontSize=48, leading=54,
        textColor=colors.HexColor("#1a1a2e"), alignment=1, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontName=font_name, fontSize=20, leading=26,
        textColor=colors.HexColor("#333355"), alignment=1, spaceAfter=10,
    )
    note_style = ParagraphStyle(
        "note", fontName=font_name, fontSize=15, leading=22,
        textColor=colors.HexColor("#222222"), alignment=0,
    )
    note_title_style = ParagraphStyle(
        "note_title", fontName=font_bold, fontSize=18, leading=24,
        textColor=colors.HexColor("#1a1a2e"), alignment=0, spaceAfter=6,
    )

    story.append(Paragraph("抵抗値系列 早見表", title_style))
    story.append(Paragraph(
        "E12 ・ E24 ・ E48（数値は下表のとおり10倍・100倍表記／小数点なし）",
        subtitle_style,
    ))
    story.append(Spacer(1, 5 * mm))

    # ---------- メインテーブル ----------
    max_e48 = max(len(r[2]) for r in RESISTOR_ROWS)
    header = ["E12", "E24"] + [f"E48-{i + 1}" for i in range(max_e48)]

    header_style = ParagraphStyle(
        "header", fontName=font_bold, fontSize=25, leading=29,
        textColor=colors.white, alignment=1,
    )
    e12_style = ParagraphStyle(
        "e12cell", fontName=font_bold, fontSize=30, leading=34,
        textColor=colors.HexColor("#8B0000"), alignment=1,
    )
    e24_style = ParagraphStyle(
        "e24cell", fontName=font_bold, fontSize=28, leading=32,
        textColor=colors.HexColor("#00529B"), alignment=1,
    )
    e48_style = ParagraphStyle(
        "e48cell", fontName=font_name, fontSize=23, leading=27,
        textColor=colors.HexColor("#222222"), alignment=1,
    )

    tbl_data = [[Paragraph(h, header_style) for h in header]]
    for e12, e24, e48list in RESISTOR_ROWS:
        padded = e48list + [None] * (max_e48 - len(e48list))
        row = [Paragraph(cell(e12), e12_style), Paragraph(cell(e24), e24_style)]
        row += [Paragraph(cell(v), e48_style) for v in padded]
        tbl_data.append(row)

    avail_width = page_w - 30 * mm
    col_widths = [avail_width * 0.13, avail_width * 0.13] + \
                 [avail_width * 0.745 / max_e48] * max_e48
    row_heights = [19 * mm] + [17 * mm] * len(RESISTOR_ROWS)

    table = Table(tbl_data, colWidths=col_widths, rowHeights=row_heights, hAlign="CENTER")
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#888888")),
        ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#1a1a2e")),
        ("BACKGROUND", (0, 1), (1, -1), colors.HexColor("#FFF3F0")),
    ]
    for i in range(1, len(tbl_data)):
        bg = colors.HexColor("#F0F5FF") if i % 2 == 0 else colors.white
        style_cmds.append(("BACKGROUND", (2, i), (-1, i), bg))
    table.setStyle(TableStyle(style_cmds))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    # ---------- 凡例 ----------
    legend_style = ParagraphStyle(
        "legend", fontName=font_name, fontSize=17, leading=22, alignment=0,
    )
    legend_table = Table(
        [[
            Paragraph('<font color="#8B0000"><b>■ E12</b></font>　基本系列（許容差 ±10%）', legend_style),
            Paragraph('<font color="#00529B"><b>■ E24</b></font>　E12との重複を除いた追加系列（許容差 ±5%）', legend_style),
            Paragraph('<font color="#222222"><b>■ E48</b></font>　精密系列（許容差 ±2%）／各E12値の区間ごとに配置', legend_style),
        ]],
        colWidths=[avail_width / 3] * 3,
    )
    legend_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(legend_table)
    story.append(Spacer(1, 8 * mm))

    # ---------- 注記 + カラーコード表(2カラムレイアウト) ----------
    note_text = """
<b>【表の数値の読み方】</b><br/>
・見やすくするため、E12・E24 は元の値を<b>10倍</b>、E48 は元の値を<b>100倍</b>して小数点をなくして表記しています。<br/>
・実際の抵抗値を求めるには、表の数値を <b>E12・E24 は 1/10、E48 は 1/100</b> してから、必要な10のべき乗<br/>
　（×0.1, ×1, ×10, ×100, ×1kΩ, ×10kΩ…）を掛けてください。<br/>
　例）E12の「22」→ 0.1をかけて 2.2 → 2.2kΩ を作るなら ×1000 = 2.2kΩ<br/>
　例）E48の「226」→ 0.01をかけて 2.26 → 2.26kΩ を作るなら ×1000 = 2.26kΩ<br/>
・E48の各値は、同じ行のE12の値以上、次の行のE12の値未満の範囲に含まれる値を並べたものです<br/>
　（列数がそろわない行は空欄になります）。
"""

    cc_header_style = ParagraphStyle(
        "cc_header", fontName=font_bold, fontSize=13, leading=16,
        textColor=colors.white, alignment=1,
    )
    cc_cell_style = ParagraphStyle(
        "cc_cell", fontName=font_name, fontSize=12, leading=15,
        textColor=colors.HexColor("#111111"), alignment=1,
    )
    cc_cell_style_w = ParagraphStyle(
        "cc_cell_w", fontName=font_name, fontSize=12, leading=15,
        textColor=colors.white, alignment=1,
    )

    cc_header_row = [Paragraph(h, cc_header_style) for h in ("色", "数字", "乗数", "許容差")]
    cc_data = [cc_header_row]
    cc_bg = [colors.HexColor("#1a1a2e")]
    for name, digit, mult, tol, hexcolor, is_white_text in COLOR_CODE_ROWS:
        name_style = cc_cell_style_w if is_white_text else cc_cell_style
        cc_data.append([
            Paragraph(name, name_style),
            Paragraph(digit, cc_cell_style),
            Paragraph(mult, cc_cell_style),
            Paragraph(tol, cc_cell_style),
        ])
        cc_bg.append(colors.HexColor(hexcolor))

    right_col_width = avail_width * 0.34
    cc_col_widths = [right_col_width * 0.18, right_col_width * 0.24,
                      right_col_width * 0.34, right_col_width * 0.24]
    cc_row_heights = [8 * mm] + [7 * mm] * len(COLOR_CODE_ROWS)

    cc_table = Table(cc_data, colWidths=cc_col_widths, rowHeights=cc_row_heights, hAlign="LEFT")
    cc_style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#666666")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#1a1a2e")),
        ("BACKGROUND", (1, 0), (-1, 0), colors.HexColor("#1a1a2e")),
    ]
    for i, bg in enumerate(cc_bg):
        cc_style_cmds.append(("BACKGROUND", (0, i), (0, i), bg))
    cc_table.setStyle(TableStyle(cc_style_cmds))

    cc_block = [
        Paragraph("参考：抵抗器カラーコード表", note_title_style),
        Spacer(1, 2 * mm),
        cc_table,
    ]

    left_col_width = avail_width * 0.62
    two_col_table = Table(
        [[Paragraph(note_text, note_style), cc_block]],
        colWidths=[left_col_width, right_col_width],
    )
    two_col_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (1, 0), (1, 0), 10 * mm),
    ]))
    story.append(two_col_table)

    return story


def generate_poster(output_path, pagesize_name="A2", font_path=None):
    page_size = landscape(PAGE_SIZES[pagesize_name])
    page_w, page_h = page_size

    jp_font_path = find_japanese_font(font_path)
    if jp_font_path is None:
        print(
            "警告: 日本語TrueTypeフォントが見つかりませんでした。\n"
            "      --font-path で明示的に指定するか、\n"
            "      'sudo apt-get install fonts-ipafont-gothic' 等でインストールしてください。",
            file=sys.stderr,
        )
        sys.exit(1)

    font_name, font_bold = "JPFont", "JPFontBold"
    pdfmetrics.registerFont(TTFont(font_name, jp_font_path))
    pdfmetrics.registerFont(TTFont(font_bold, jp_font_path))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
    )
    story = build_story(page_w, page_h, font_name, font_bold)
    doc.build(story)
    print(f"ポスターPDFを生成しました: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="抵抗値系列(E12/E24/E48)早見ポスターPDFを生成します。"
    )
    parser.add_argument(
        "-o", "--output",
        default="output/resistor_series_poster.pdf",
        help="出力PDFのパス (デフォルト: output/resistor_series_poster.pdf)",
    )
    parser.add_argument(
        "--pagesize",
        choices=sorted(PAGE_SIZES.keys()),
        default="A2",
        help="用紙サイズ (デフォルト: A2、横向きで出力)",
    )
    parser.add_argument(
        "--font-path",
        default=None,
        help="使用する日本語TrueTypeフォント(.ttf)のパスを明示的に指定",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    generate_poster(args.output, args.pagesize, args.font_path)


if __name__ == "__main__":
    main()
