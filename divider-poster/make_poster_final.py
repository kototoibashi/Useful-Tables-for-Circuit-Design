# -*- coding: utf-8 -*-
import json
import math
from reportlab.lib.pagesizes import A2, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white

pdfmetrics.registerFont(TTFont('IPAGothic', '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'))

with open('./table_data_grid_1_48.json', encoding='utf-8') as f:
    GRID_DATA = json.load(f)

with open('./list_49_50_grouped.json', encoding='utf-8') as f:
    LIST_DATA = json.load(f)  # small grouped list, 48.7-50%, used as footer text only

OFFSETS = [0.0, 0.25, 0.5, 0.75]
OFFSET_LABELS = ['+0.0%', '+0.25%', '+0.5%', '+0.75%']

grid_groups = [
    [str(r) for r in range(1, 17)],
    [str(r) for r in range(17, 33)],
    [str(r) for r in range(33, 49)],
]

COL_BG        = white
COL_TEXT      = black
COL_MUTED     = HexColor('#555555')
COL_HEADER_BG = HexColor('#eeeeee')
COL_GRID      = HexColor('#dddddd')

BORDER_E12 = HexColor('#1c5a96')
BORDER_E24 = HexColor('#b8860b')
BORDER_E48 = HexColor('#c1440e')
BORDER_NA  = HexColor('#c0392b')

BORDER_COLORS = {'E12': BORDER_E12, 'E24': BORDER_E24, 'E48': BORDER_E48}
BORDER_WIDTH = 1.6

def fit_font(text, max_w, max_h, start=60, min_size=5.0):
    size = min(start, max_h)
    while size > min_size and pdfmetrics.stringWidth(text, 'IPAGothic', size) > max_w:
        size -= 0.2
    return size

page_w, page_h = landscape(A2)
c = canvas.Canvas('./voltage_divider_poster_final.pdf', pagesize=landscape(A2))

margin = 14*mm
panel_gap = 8*mm

c.setFillColor(COL_BG)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

title_y = page_h - margin - 8*mm
c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 17)
c.drawString(margin, title_y, "2直列抵抗 分圧比 早見表")
c.setFont('IPAGothic', 8.5)
c.setFillColor(COL_MUTED)
c.drawString(margin, title_y - 6.5*mm,
    "Vout = Vin × R2/(R1+R2)　｜　数字は R1-R2（整数表記・そのまま抵抗値として使用可）　｜　"
    "枠線の色 = 使用系列／E48は下線／該当なしは斜線（±0.125%以内で判定）　｜　49%以上は下部参照")

legend_y = title_y
line_len = 6*mm
gap = 36*mm
c.setFont('IPAGothic', 8.5)

lx = page_w - margin - 150*mm
legend_defs = [
    ("E12", BORDER_E12, 'plain'),
    ("E24", BORDER_E24, 'plain'),
    ("E48", BORDER_E48, 'underline'),
    ("該当なし", BORDER_NA, 'hatch'),
]
for i, (label, col, style) in enumerate(legend_defs):
    x0 = lx + i*gap
    c.setStrokeColor(col)
    c.setLineWidth(2.4)
    c.line(x0, legend_y - 2*mm, x0 + line_len, legend_y - 2*mm)
    if style == 'underline':
        c.setStrokeColor(black)
        c.setLineWidth(1.0)
        c.line(x0, legend_y - 3.2*mm, x0 + line_len, legend_y - 3.2*mm)
    if style == 'hatch':
        c.setStrokeColor(col)
        c.setLineWidth(1.0)
        c.line(x0, legend_y - 3.6*mm, x0 + line_len, legend_y - 0.4*mm)
    c.setFillColor(COL_TEXT)
    c.drawString(x0 + line_len + 2*mm, legend_y - 3*mm, label)

grid_top = title_y - 15*mm
grid_bottom = margin + 10*mm
total_grid_w = page_w - 2*margin - 2*panel_gap
panel_w = total_grid_w / 3

label_col_w = 20*mm
header_row_h = 11*mm

# ---------- grid (table) panel ----------
def draw_grid_panel(panel_idx, rows_subset):
    px_left = margin + panel_idx*(panel_w + panel_gap)
    px_right = px_left + panel_w

    n_rows = len(rows_subset)
    data_col_w = (panel_w - label_col_w) / len(OFFSETS)
    data_row_h = (grid_top - header_row_h - grid_bottom) / n_rows

    c.setFont('IPAGothic', 9.5)
    c.setFillColor(COL_MUTED)
    c.drawString(px_left, grid_top + 3*mm, f"{rows_subset[0]}%〜{rows_subset[-1]}%")

    hy0 = grid_top - header_row_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(px_left, hy0, label_col_w, header_row_h, fill=1, stroke=0)
    c.setFillColor(COL_TEXT)
    txt = "分圧比"
    fsize = fit_font(txt, label_col_w - 2*mm, header_row_h - 2*mm, start=14)
    c.setFont('IPAGothic', fsize)
    c.drawCentredString(px_left + label_col_w/2, hy0 + header_row_h/2 - fsize*0.32, txt)

    for i, lbl in enumerate(OFFSET_LABELS):
        x0 = px_left + label_col_w + i*data_col_w
        c.setFillColor(COL_HEADER_BG)
        c.rect(x0, hy0, data_col_w, header_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        fsize = fit_font(lbl, data_col_w - 2*mm, header_row_h - 2*mm, start=14)
        c.setFont('IPAGothic', fsize)
        c.drawCentredString(x0 + data_col_w/2, hy0 + header_row_h/2 - fsize*0.32, lbl)

    for r, pct in enumerate(rows_subset):
        ry0 = hy0 - (r+1)*data_row_h
        c.setFillColor(COL_HEADER_BG)
        c.rect(px_left, ry0, label_col_w, data_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        fsize = fit_font(pct, label_col_w - 2*mm, data_row_h - 2*mm, start=20)
        c.setFont('IPAGothic', fsize)
        c.drawCentredString(px_left + label_col_w/2, ry0 + data_row_h/2 - fsize*0.32, pct)

        for cidx in range(len(OFFSETS)):
            x0 = px_left + label_col_w + cidx*data_col_w
            cell = GRID_DATA[pct][cidx]

            c.setFillColor(white)
            c.rect(x0, ry0, data_col_w, data_row_h, fill=1, stroke=0)

            if not cell['ok']:
                border = BORDER_NA
                c.setStrokeColor(border)
                c.setLineWidth(BORDER_WIDTH)
                c.rect(x0, ry0, data_col_w, data_row_h, fill=0, stroke=1)
                c.setLineWidth(1.2)
                inset = 1.0*mm
                c.line(x0+inset, ry0+inset, x0+data_col_w-inset, ry0+data_row_h-inset)
            else:
                src = cell['src']
                border = BORDER_COLORS[src]
                main_text = f"{cell['r1']}-{cell['r2']}"

                c.setStrokeColor(border)
                c.setLineWidth(BORDER_WIDTH)
                c.rect(x0, ry0, data_col_w, data_row_h, fill=0, stroke=1)

                c.setFillColor(COL_TEXT)
                max_w = data_col_w - 1.6*mm
                max_h = data_row_h - 1.6*mm
                fsize = fit_font(main_text, max_w, max_h, start=40)
                c.setFont('IPAGothic', fsize)
                ty = ry0 + data_row_h/2 - fsize*0.32
                c.drawCentredString(x0 + data_col_w/2, ty, main_text)

                if src == 'E48':
                    tw = pdfmetrics.stringWidth(main_text, 'IPAGothic', fsize)
                    ux0 = x0 + data_col_w/2 - tw/2
                    ux1 = x0 + data_col_w/2 + tw/2
                    uy = ty - fsize*0.12
                    c.setStrokeColor(black)
                    c.setLineWidth(max(0.8, fsize*0.045))
                    c.line(ux0, uy, ux1, uy)

    c.setStrokeColor(COL_GRID)
    c.setLineWidth(0.4)
    xs = [px_left, px_left+label_col_w] + [px_left+label_col_w+i*data_col_w for i in range(1, len(OFFSETS)+1)]
    for x in xs:
        c.line(x, grid_bottom, x, grid_top)
    ys = [grid_top, hy0] + [hy0 - (r+1)*data_row_h for r in range(n_rows)]
    for y in ys:
        c.line(px_left, y, px_right, y)


# ---------- list panel (40-50%, E12/E24 only) ----------
def draw_list_panel(panel_idx, entries):
    px_left = margin + panel_idx*(panel_w + panel_gap)
    px_right = px_left + panel_w

    n_sub = 1
    per_col = math.ceil(len(entries)/n_sub)
    sub_w = panel_w / n_sub

    c.setFont('IPAGothic', 9.5)
    c.setFillColor(COL_MUTED)
    c.drawString(px_left, grid_top + 3*mm, "49%〜50%（E48まで開放しても48.94%〜50.00%は完全に空白）")

    hy0 = grid_top - header_row_h
    n_rows = per_col
    data_row_h = (grid_top - header_row_h - grid_bottom) / n_rows

    ratio_col_w = sub_w * 0.42
    combo_col_w = sub_w - ratio_col_w

    for s in range(n_sub):
        sx_left = px_left + s*sub_w
        # header
        c.setFillColor(COL_HEADER_BG)
        c.rect(sx_left, hy0, sub_w, header_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        h1 = "分圧比"
        f1 = fit_font(h1, ratio_col_w - 1.5*mm, header_row_h - 2*mm, start=12)
        c.setFont('IPAGothic', f1)
        c.drawCentredString(sx_left + ratio_col_w/2, hy0 + header_row_h/2 - f1*0.32, h1)
        h2 = "組み合わせ"
        f2 = fit_font(h2, combo_col_w - 1.5*mm, header_row_h - 2*mm, start=12)
        c.setFont('IPAGothic', f2)
        c.drawCentredString(sx_left + ratio_col_w + combo_col_w/2, hy0 + header_row_h/2 - f2*0.32, h2)

        sub_entries = entries[s*per_col:(s+1)*per_col]
        for r in range(n_rows):
            ry0 = hy0 - (r+1)*data_row_h
            if r < len(sub_entries):
                e = sub_entries[r]
                ratio_text = f"{e['ratio']:.2f}%"
                combo_text = f"{e['r1']}-{e['r2']}"
                border = BORDER_COLORS[e['src']]
            else:
                ratio_text = ""
                combo_text = ""
                border = None

            # ratio cell
            c.setFillColor(white)
            c.rect(sx_left, ry0, ratio_col_w, data_row_h, fill=1, stroke=0)
            if ratio_text:
                c.setFillColor(COL_TEXT)
                fsize = fit_font(ratio_text, ratio_col_w - 1.6*mm, data_row_h - 1.6*mm, start=30)
                c.setFont('IPAGothic', fsize)
                c.drawCentredString(sx_left + ratio_col_w/2, ry0 + data_row_h/2 - fsize*0.32, ratio_text)

            # combo cell
            cx0 = sx_left + ratio_col_w
            c.setFillColor(white)
            c.rect(cx0, ry0, combo_col_w, data_row_h, fill=1, stroke=0)
            if combo_text:
                c.setStrokeColor(border)
                c.setLineWidth(BORDER_WIDTH)
                c.rect(cx0, ry0, combo_col_w, data_row_h, fill=0, stroke=1)
                c.setFillColor(COL_TEXT)
                fsize = fit_font(combo_text, combo_col_w - 1.6*mm, data_row_h - 1.6*mm, start=30)
                c.setFont('IPAGothic', fsize)
                cty = ry0 + data_row_h/2 - fsize*0.32
                c.drawCentredString(cx0 + combo_col_w/2, cty, combo_text)
                if e['src'] == 'E48':
                    tw = pdfmetrics.stringWidth(combo_text, 'IPAGothic', fsize)
                    ux0 = cx0 + combo_col_w/2 - tw/2
                    ux1 = cx0 + combo_col_w/2 + tw/2
                    uy = cty - fsize*0.12
                    c.setStrokeColor(black)
                    c.setLineWidth(max(0.8, fsize*0.045))
                    c.line(ux0, uy, ux1, uy)

        # grid lines for this sub-column
        c.setStrokeColor(COL_GRID)
        c.setLineWidth(0.4)
        for x in [sx_left, sx_left+ratio_col_w, sx_left+sub_w]:
            c.line(x, grid_bottom, x, grid_top)
        ys = [grid_top, hy0] + [hy0 - (r+1)*data_row_h for r in range(n_rows)]
        for y in ys:
            c.line(sx_left, y, sx_left+sub_w, y)


draw_grid_panel(0, grid_groups[0])
draw_grid_panel(1, grid_groups[1])
draw_grid_panel(2, grid_groups[2])

list_text = "　".join(f"{e['ratio']:.2f}%→{e['r1']}-{e['r2']}({e['src']})" for e in LIST_DATA)

foot_y = grid_bottom - 6*mm
c.setFillColor(COL_MUTED)
c.setFont('IPAGothic', 7.5)
c.drawString(margin, foot_y,
    "使い方：分圧比の整数部で行、小数部を0.25%刻みで丸めて列を選び、セルの数字をそのままR1・R2として使用（桁は用途に応じて調整）")
c.drawString(margin, foot_y - 4.2*mm,
    f"参考（49%〜50%・表には含めず）：{list_text}　｜　48.94%〜50.00%はE48まで開放しても組み合わせが存在しません")

c.showPage()
c.save()
print("saved. grid groups:", [len(g) for g in grid_groups])
