# -*- coding: utf-8 -*-
"""
E6系列 2直列抵抗 分圧比 全数表 (1%〜50%)

Vout = Vin * R2/(R1+R2) の分圧比を、E6系列の抵抗2本(R1, R2)だけで
実現できる組み合わせについて 1%〜50% の範囲ですべて洗い出し、
A2横ポスターPDFとして出力する。

E12/E24/E48を使う divider-poster と違い、目標の1%刻みグリッドに
「一番近い値」を当てはめるのではなく、E6の2本組み合わせで実際に
出せる分圧比を過不足なくそのまま列挙する。
"""
import math
from reportlab.lib.pagesizes import A2, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white

pdfmetrics.registerFont(TTFont('IPAGothic', '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'))

E6 = [10, 15, 22, 33, 47, 68]
PCT_MIN, PCT_MAX = 1.0, 50.0
DECADE_SHIFTS = range(-4, 5)


def fmt_r(v):
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:g}"


def find_all_ratios():
    """E6の2本(R1, R2、任意の10のべき乗ずれを許容)で 1%<=pct<=50% に
    収まる分圧比をすべて求め、各分圧比について最も簡潔な組み合わせ
    (桁ずれが小さく、値が小さいもの)を1つ選んで返す。"""
    best = {}
    for ei in E6:
        for ej in E6:
            for shift in DECADE_SHIFTS:
                r1 = ei * (10 ** shift)
                r2 = ej
                pct = r2 / (r1 + r2) * 100
                if not (PCT_MIN <= pct <= PCT_MAX):
                    continue
                key = round(pct, 3)
                gap = abs(shift)
                cand = (r1, r2, gap)
                cur = best.get(key)
                if cur is None or (gap, max(r1, r2)) < (cur[2], max(cur[0], cur[1])):
                    best[key] = cand
    return sorted((pct, r1, r2) for pct, (r1, r2, _gap) in best.items())


ENTRIES = find_all_ratios()

COL_BG        = white
COL_TEXT      = black
COL_MUTED     = HexColor('#555555')
COL_HEADER_BG = HexColor('#eeeeee')
COL_GRID      = HexColor('#dddddd')
BORDER_E6     = HexColor('#1c8a5a')
BORDER_WIDTH  = 1.6


def fit_font(text, max_w, max_h, start=40, min_size=5.0):
    size = min(start, max_h)
    while size > min_size and pdfmetrics.stringWidth(text, 'IPAGothic', size) > max_w:
        size -= 0.2
    return size


page_w, page_h = landscape(A2)
c = canvas.Canvas('./e6_divider_poster.pdf', pagesize=landscape(A2))

margin = 14 * mm

c.setFillColor(COL_BG)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

title_y = page_h - margin - 8 * mm
c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 17)
c.drawString(margin, title_y, "E6系列 2直列抵抗 分圧比 全数表（1%〜50%）")
c.setFont('IPAGothic', 8.5)
c.setFillColor(COL_MUTED)
c.drawString(margin, title_y - 6.5 * mm,
    "Vout = Vin × R2/(R1+R2)　｜　E6系列の抵抗2本で実際に作れる分圧比を過不足なく列挙（グリッドへの近似ではない）　｜　"
    f"該当数 {len(ENTRIES)} 件")
c.drawString(margin, title_y - 11.5 * mm,
    "50%を超える比率が必要な場合：(100-x)%の行のR1とR2を入れ替えれば厳密にx%が得られる（R1/(R1+R2) = 1 - R2/(R1+R2) のため）")

panel_top = title_y - 20 * mm
panel_bottom = margin + 10 * mm

N_COLS = 3
n_rows = math.ceil(len(ENTRIES) / N_COLS)
total_w = page_w - 2 * margin
col_gap = 8 * mm
col_w = (total_w - (N_COLS - 1) * col_gap) / N_COLS

ratio_col_w = col_w * 0.42
combo_col_w = col_w - ratio_col_w
header_row_h = 11 * mm
data_row_h = (panel_top - header_row_h - panel_bottom) / n_rows

for col in range(N_COLS):
    cx_left = margin + col * (col_w + col_gap)
    entries_col = ENTRIES[col * n_rows:(col + 1) * n_rows]

    hy0 = panel_top - header_row_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(cx_left, hy0, col_w, header_row_h, fill=1, stroke=0)
    c.setFillColor(COL_TEXT)
    h1 = "分圧比"
    f1 = fit_font(h1, ratio_col_w - 1.5 * mm, header_row_h - 2 * mm, start=13)
    c.setFont('IPAGothic', f1)
    c.drawCentredString(cx_left + ratio_col_w / 2, hy0 + header_row_h / 2 - f1 * 0.32, h1)
    h2 = "組み合わせ（R1-R2）"
    f2 = fit_font(h2, combo_col_w - 1.5 * mm, header_row_h - 2 * mm, start=13)
    c.setFont('IPAGothic', f2)
    c.drawCentredString(cx_left + ratio_col_w + combo_col_w / 2, hy0 + header_row_h / 2 - f2 * 0.32, h2)

    for r in range(n_rows):
        ry0 = hy0 - (r + 1) * data_row_h
        ratio_text = combo_text = ""
        if r < len(entries_col):
            pct, r1, r2 = entries_col[r]
            ratio_text = f"{pct:.3f}%"
            combo_text = f"{fmt_r(r1)}-{fmt_r(r2)}"

        c.setFillColor(white)
        c.rect(cx_left, ry0, ratio_col_w, data_row_h, fill=1, stroke=0)
        if ratio_text:
            c.setFillColor(COL_TEXT)
            fsize = fit_font(ratio_text, ratio_col_w - 1.6 * mm, data_row_h - 1.6 * mm, start=26)
            c.setFont('IPAGothic', fsize)
            c.drawCentredString(cx_left + ratio_col_w / 2, ry0 + data_row_h / 2 - fsize * 0.32, ratio_text)

        cx0 = cx_left + ratio_col_w
        c.setFillColor(white)
        c.rect(cx0, ry0, combo_col_w, data_row_h, fill=1, stroke=0)
        if combo_text:
            c.setStrokeColor(BORDER_E6)
            c.setLineWidth(BORDER_WIDTH)
            c.rect(cx0, ry0, combo_col_w, data_row_h, fill=0, stroke=1)
            c.setFillColor(COL_TEXT)
            fsize = fit_font(combo_text, combo_col_w - 1.6 * mm, data_row_h - 1.6 * mm, start=26)
            c.setFont('IPAGothic', fsize)
            c.drawCentredString(cx0 + combo_col_w / 2, ry0 + data_row_h / 2 - fsize * 0.32, combo_text)

    c.setStrokeColor(COL_GRID)
    c.setLineWidth(0.4)
    for x in (cx_left, cx_left + ratio_col_w, cx_left + col_w):
        c.line(x, panel_bottom, x, panel_top)
    for r in range(n_rows + 1):
        y = hy0 - r * data_row_h if r > 0 else panel_top
        c.line(cx_left, y, cx_left + col_w, y)
    c.line(cx_left, hy0, cx_left + col_w, hy0)

foot_y = panel_bottom - 6 * mm
c.setFillColor(COL_MUTED)
c.setFont('IPAGothic', 7.5)
c.drawString(margin, foot_y,
    "使い方：組み合わせの数字をそのままR1・R2として使用（桁は用途に応じて×0.1〜×1000などで調整）")

c.showPage()
c.save()
print(f"saved. {len(ENTRIES)} ratios (1%-50%) across {N_COLS} columns x {n_rows} rows")
