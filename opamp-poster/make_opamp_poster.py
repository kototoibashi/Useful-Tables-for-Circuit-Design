# -*- coding: utf-8 -*-
import json
from reportlab.lib.pagesizes import A2, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white

pdfmetrics.registerFont(TTFont('IPAGothic', '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'))

with open('./opamp_data.json', encoding='utf-8') as f:
    DATA = json.load(f)

R1_options = [39, 51, 100, 200]
gains = [1, 2, 3, 4, 5, 7.5, 10]

COL_BG        = white
COL_TEXT      = black
COL_MUTED     = HexColor('#555555')
COL_HEADER_BG = HexColor('#eeeeee')
COL_GRID      = HexColor('#dddddd')
COL_BOX       = HexColor('#f4f4f4')

BORDER_E12 = HexColor('#1c5a96')
BORDER_E24 = HexColor('#b8860b')
BORDER_E48 = HexColor('#c1440e')
BORDER_COLORS = {'E12': BORDER_E12, 'E24': BORDER_E24, 'E48': BORDER_E48}
BORDER_WIDTH = 1.4

def fit_font(text, max_w, max_h, start=40, min_size=5.0):
    size = min(start, max_h)
    while size > min_size and pdfmetrics.stringWidth(text, 'IPAGothic', size) > max_w:
        size -= 0.2
    return size

def fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:g}"

page_w, page_h = landscape(A2)
c = canvas.Canvas('./opamp_poster.pdf', pagesize=landscape(A2))
margin = 14*mm

c.setFillColor(COL_BG)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

# ============================================================
# Title
# ============================================================
title_y = page_h - margin - 8*mm
c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 17)
c.drawString(margin, title_y, "オペアンプ増幅回路 抵抗値早見表")
c.setFont('IPAGothic', 8.5)
c.setFillColor(COL_MUTED)
c.drawString(margin, title_y - 6.5*mm,
    "入力インピーダンス Zin(=R1) を 39 / 51 / 100 / 200 に固定し、増幅率 Av に対する R2 を掲載　｜　"
    "枠線の色 = 使用系列／E48は下線　｜　[E24代替]はE48が最良のときのE24縮小版")

legend_y = title_y
line_len = 6*mm
gap = 34*mm
lx = page_w - margin - 130*mm
legend_defs = [("E12", BORDER_E12, False), ("E24", BORDER_E24, False), ("E48", BORDER_E48, True)]
c.setFont('IPAGothic', 8.5)
for i, (label, col, underline) in enumerate(legend_defs):
    x0 = lx + i*gap
    c.setStrokeColor(col)
    c.setLineWidth(2.4)
    c.line(x0, legend_y - 2*mm, x0 + line_len, legend_y - 2*mm)
    if underline:
        c.setStrokeColor(black)
        c.setLineWidth(1.0)
        c.line(x0, legend_y - 3.2*mm, x0 + line_len, legend_y - 3.2*mm)
    c.setFillColor(COL_TEXT)
    c.drawString(x0 + line_len + 2*mm, legend_y - 3*mm, label)

# ============================================================
# Circuit diagrams
# ============================================================
def draw_resistor(cv, x1, y1, x2, y2, label, sub_label=None):
    cv.setStrokeColor(black)
    cv.setLineWidth(1.1)
    dx, dy = x2-x1, y2-y1
    length = (dx**2+dy**2)**0.5
    n_zig = 6
    body_frac = 0.6
    lead = length*(1-body_frac)/2
    ux, uy = dx/length, dy/length
    px, py = -uy, ux
    amp = 2.6*mm
    body_len = length*body_frac
    start_x = x1+ux*lead
    start_y = y1+uy*lead
    cv.line(x1, y1, start_x, start_y)
    pts = []
    seg = body_len/n_zig
    for i in range(n_zig+1):
        bx = start_x + ux*seg*i
        by = start_y + uy*seg*i
        if i == 0 or i == n_zig:
            off = 0
        else:
            off = amp if i % 2 == 1 else -amp
        pts.append((bx+px*off, by+py*off))
    p = cv.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    cv.drawPath(p, stroke=1, fill=0)
    end_x = start_x+ux*body_len
    end_y = start_y+uy*body_len
    cv.line(end_x, end_y, x2, y2)
    cv.setFillColor(black)
    mx, my = (x1+x2)/2, (y1+y2)/2
    if abs(dy) < 1e-6:
        fsize = fit_font(label, length*0.9, 6*mm, start=11)
        cv.setFont('IPAGothic', fsize)
        cv.drawCentredString(mx, my+3.5*mm, label)
        if sub_label:
            cv.setFont('IPAGothic', 6.5)
            cv.setFillColor(COL_MUTED)
            cv.drawCentredString(mx, my-6.5*mm, sub_label)
    else:
        fsize = fit_font(label, 20*mm, 6*mm, start=11)
        cv.setFont('IPAGothic', fsize)
        cv.drawString(mx+5*mm, my-1.5*mm, label)
        if sub_label:
            cv.setFont('IPAGothic', 6.5)
            cv.setFillColor(COL_MUTED)
            cv.drawString(mx+5*mm, my-7*mm, sub_label)

def draw_gnd(cv, x, y):
    cv.setStrokeColor(black)
    cv.setLineWidth(1.0)
    cv.line(x, y, x, y-3*mm)
    widths = [6*mm, 4*mm, 2*mm]
    for i, w in enumerate(widths):
        yy = y-3*mm-i*1.6*mm
        cv.line(x-w/2, yy, x+w/2, yy)

def draw_opamp(cv, x_tip, y_mid, size, plus_top):
    x_base = x_tip - size*1.3
    y_top = y_mid + size/2
    y_bot = y_mid - size/2
    p = cv.beginPath()
    p.moveTo(x_base, y_top)
    p.lineTo(x_base, y_bot)
    p.lineTo(x_tip, y_mid)
    p.close()
    cv.setStrokeColor(black)
    cv.setLineWidth(1.3)
    cv.setFillColor(white)
    cv.drawPath(p, stroke=1, fill=1)
    cv.setFillColor(black)
    cv.setFont('IPAGothic', 10)
    top_sym = "+" if plus_top else "\u2212"
    bot_sym = "\u2212" if plus_top else "+"
    cv.drawString(x_base+2*mm, y_top-5*mm, top_sym)
    cv.drawString(x_base+2*mm, y_bot+2.5*mm, bot_sym)
    return x_base, y_top, y_bot

def draw_inverting_circuit(cv, ox, oy, w, h):
    cy = oy + h*0.30
    x_vin = ox + 8*mm
    x_r1_start = ox + 18*mm
    x_r1_end = ox + 52*mm
    x_opamp_tip = ox + w*0.72
    opamp_size = h*0.34
    x_base, y_top, y_bot = draw_opamp(cv, x_opamp_tip, cy, opamp_size, plus_top=False)

    cv.setFont('IPAGothic', 10)
    cv.setFillColor(black)
    cv.drawString(x_vin-6*mm, cy+3*mm, "Vin")
    cv.line(x_vin, cy, x_r1_start, cy)
    draw_resistor(cv, x_r1_start, cy, x_r1_end, cy, "R1")
    cv.line(x_r1_end, cy, x_r1_end, y_top)
    cv.line(x_r1_end, y_top, x_base, y_top)

    cv.line(x_base-6*mm, y_bot, x_base, y_bot)
    draw_gnd(cv, x_base-6*mm, y_bot)

    fb_y = cy + opamp_size*1.15
    x_out = x_opamp_tip + 6*mm
    cv.line(x_r1_end, cy, x_r1_end, fb_y)
    draw_resistor(cv, x_r1_end, fb_y, x_out, fb_y, "R2")
    cv.line(x_out, fb_y, x_out, cy)

    x_vout = ox + w - 6*mm
    cv.line(x_opamp_tip, cy, x_vout, cy)
    cv.setFont('IPAGothic', 10)
    cv.drawString(x_vout+1.5*mm, cy-1.5*mm, "Vout")

    cv.setFont('IPAGothic', 10.5)
    cv.setFillColor(COL_TEXT)
    cv.drawCentredString(ox+w/2, oy+h-4*mm, "反転増幅　Av = \u2212R2/R1　（Zin = R1）")

def draw_noninverting_circuit(cv, ox, oy, w, h):
    cy = oy + h*0.30
    x_vin = ox + 8*mm
    x_opamp_tip = ox + w*0.72
    opamp_size = h*0.34
    x_base, y_top, y_bot = draw_opamp(cv, x_opamp_tip, cy, opamp_size, plus_top=True)

    cv.setFont('IPAGothic', 10)
    cv.setFillColor(black)
    cv.drawString(x_vin-6*mm, y_top-1*mm, "Vin")
    cv.line(x_vin, y_top-1*mm+1.5*mm, x_base, y_top-1*mm+1.5*mm)

    x_r1_end = x_base
    x_r1_start = x_base - 34*mm
    r1_y = y_bot
    draw_resistor(cv, x_r1_start, r1_y, x_r1_end, r1_y, "R1")
    cv.line(x_r1_start, r1_y, x_r1_start, r1_y-8*mm)
    draw_gnd(cv, x_r1_start, r1_y-8*mm)

    fb_y = cy + opamp_size*1.15
    x_out = x_opamp_tip + 6*mm
    cv.line(x_r1_end, r1_y, x_r1_end, fb_y)
    draw_resistor(cv, x_r1_end, fb_y, x_out, fb_y, "R2")
    cv.line(x_out, fb_y, x_out, cy)

    x_vout = ox + w - 6*mm
    cv.line(x_opamp_tip, cy, x_vout, cy)
    cv.setFont('IPAGothic', 10)
    cv.drawString(x_vout+1.5*mm, cy-1.5*mm, "Vout")

    cv.setFont('IPAGothic', 10.5)
    cv.setFillColor(COL_TEXT)
    cv.drawCentredString(ox+w/2, oy+h-4*mm, "非反転増幅　Av = 1+R2/R1　（R1はGND基準）")

circuit_top = title_y - 14*mm
circuit_h = 46*mm
circuit_w = (page_w - 2*margin - 10*mm)/2
draw_inverting_circuit(c, margin, circuit_top-circuit_h, circuit_w, circuit_h)
draw_noninverting_circuit(c, margin+circuit_w+10*mm, circuit_top-circuit_h, circuit_w, circuit_h)

# ============================================================
# Scaling explanation box
# ============================================================
box_top = circuit_top - circuit_h - 4*mm
box_h = 26*mm
c.setFillColor(COL_BOX)
c.rect(margin, box_top-box_h, page_w-2*margin, box_h, fill=1, stroke=0)
c.setStrokeColor(COL_GRID)
c.setLineWidth(0.6)
c.rect(margin, box_top-box_h, page_w-2*margin, box_h, fill=0, stroke=1)

c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 10.5)
c.drawString(margin+5*mm, box_top-6*mm, "\u25c6 \u00d710\u207f スケーリングの使い方")

c.setFont('IPAGothic', 8.3)
col1_x = margin+5*mm
col2_x = margin + (page_w-2*margin)*0.51
c.drawString(col1_x, box_top-12*mm,
    "\u2460 増幅率Avは変えず、入力インピーダンスだけ変えたい → R1・R2を両方×10ⁿすればよい（比R2/R1は不変）")
c.drawString(col1_x, box_top-17*mm,
    "　例：Zin=100・Av=10（R2=1000）をZin=10kΩにしたい → R1=1000、R2=10000に置き換える（×10）")
c.drawString(col2_x, box_top-12*mm,
    "\u2461 増幅率Av自体を変えたい → 比R2/R1が変わるので×10ⁿでは済まない、表の別のAv行を参照する")
c.drawString(col2_x, box_top-17*mm,
    "　例：Av=10→Av=100にしたいなら「Av=10の行を10倍」ではなく「Av=100の行」を新たに参照する")
c.setFillColor(COL_MUTED)
c.drawString(col1_x, box_top-22.5*mm,
    "つまり「桁（インピーダンスレベル）」と「比率（ゲイン）」は独立パラメータ：桁は掛け算だけで動かせるが、ゲインは表を引き直す必要がある")

# ============================================================
# Tables
# ============================================================
table_top = box_top - box_h - 6*mm
table_bottom = margin + 8*mm
table_w = (page_w - 2*margin - 10*mm)/2
header_row_h = 11*mm
label_col_w = 20*mm
n_data_cols = len(R1_options)
data_col_w = (table_w - label_col_w) / n_data_cols
n_rows = len(gains)
data_row_h = (table_top - header_row_h - table_bottom) / n_rows

def draw_amp_table(ox, kind_key, title):
    c.setFont('IPAGothic', 10.5)
    c.setFillColor(COL_TEXT)
    c.drawString(ox, table_top+4*mm, title)

    hy0 = table_top - header_row_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(ox, hy0, label_col_w, header_row_h, fill=1, stroke=0)
    c.setFillColor(COL_TEXT)
    txt = "Av"
    fsize = fit_font(txt, label_col_w-2*mm, header_row_h-2*mm, start=13)
    c.setFont('IPAGothic', fsize)
    c.drawCentredString(ox+label_col_w/2, hy0+header_row_h/2-fsize*0.32, txt)

    for i, R1 in enumerate(R1_options):
        x0 = ox+label_col_w+i*data_col_w
        c.setFillColor(COL_HEADER_BG)
        c.rect(x0, hy0, data_col_w, header_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        lbl = f"R1={R1}"
        fsize = fit_font(lbl, data_col_w-2*mm, header_row_h-2*mm, start=13)
        c.setFont('IPAGothic', fsize)
        c.drawCentredString(x0+data_col_w/2, hy0+header_row_h/2-fsize*0.32, lbl)

    for r, g in enumerate(gains):
        ry0 = hy0-(r+1)*data_row_h
        c.setFillColor(COL_HEADER_BG)
        c.rect(ox, ry0, label_col_w, data_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        lbl = fmt(g)
        fsize = fit_font(lbl, label_col_w-2*mm, data_row_h-2*mm, start=22)
        c.setFont('IPAGothic', fsize)
        c.drawCentredString(ox+label_col_w/2, ry0+data_row_h/2-fsize*0.32, lbl)

        cell_row = DATA[kind_key][str(g)]
        for i, R1 in enumerate(R1_options):
            x0 = ox+label_col_w+i*data_col_w
            cell = cell_row[str(R1)]
            c.setFillColor(white)
            c.rect(x0, ry0, data_col_w, data_row_h, fill=1, stroke=0)

            if cell.get('follower'):
                c.setStrokeColor(COL_GRID)
                c.setLineWidth(BORDER_WIDTH)
                c.rect(x0, ry0, data_col_w, data_row_h, fill=0, stroke=1)
                c.setFillColor(COL_TEXT)
                txt = "buffer"
                fsize = fit_font(txt, data_col_w-2*mm, data_row_h-2*mm, start=16)
                c.setFont('IPAGothic', fsize)
                c.drawCentredString(x0+data_col_w/2, ry0+data_row_h/2-fsize*0.32, txt)
                continue

            border = BORDER_COLORS[cell['src']]
            main_text = f"{fmt(cell['r2'])}"
            has_alt = 'alt24' in cell

            c.setStrokeColor(border)
            c.setLineWidth(BORDER_WIDTH)
            c.rect(x0, ry0, data_col_w, data_row_h, fill=0, stroke=1)

            c.setFillColor(COL_TEXT)
            max_w = data_col_w - 1.6*mm
            top_h = data_row_h*(0.62 if has_alt else 0.9)
            fsize = fit_font(main_text, max_w, top_h, start=22)
            c.setFont('IPAGothic', fsize)
            ty = ry0 + data_row_h - fsize*1.05 if has_alt else ry0+data_row_h/2-fsize*0.32
            c.drawCentredString(x0+data_col_w/2, ty, main_text)
            if cell['src'] == 'E48' and not has_alt:
                tw = pdfmetrics.stringWidth(main_text, 'IPAGothic', fsize)
                ux0 = x0+data_col_w/2-tw/2; ux1 = x0+data_col_w/2+tw/2
                uy = ty - fsize*0.12
                c.setStrokeColor(black); c.setLineWidth(max(0.8, fsize*0.045))
                c.line(ux0, uy, ux1, uy)

            gain_text = f"実{cell['gain']:g}"
            gfsize = fit_font(gain_text, max_w, 5*mm, start=6.5)
            c.setFont('IPAGothic', gfsize)
            c.setFillColor(COL_MUTED)
            gy = ry0 + data_row_h*0.30 if has_alt else ry0 + 1.2*mm
            c.drawCentredString(x0+data_col_w/2, gy, gain_text)

            if has_alt:
                alt = cell['alt24']
                c.setStrokeColor(BORDER_E24)
                c.setLineWidth(0.9)
                c.line(x0+1.5*mm, ry0+data_row_h*0.34, x0+data_col_w-1.5*mm, ry0+data_row_h*0.34)
                alt_text = f"[E24:{fmt(alt['r2'])} 実{alt['gain']:g}]"
                afsize = fit_font(alt_text, max_w, 5*mm, start=6.5)
                c.setFont('IPAGothic', afsize)
                c.setFillColor(BORDER_E24)
                c.drawCentredString(x0+data_col_w/2, ry0+1.4*mm, alt_text)

    c.setStrokeColor(COL_GRID)
    c.setLineWidth(0.4)
    xs = [ox, ox+label_col_w]+[ox+label_col_w+i*data_col_w for i in range(1, n_data_cols+1)]
    for x in xs:
        c.line(x, table_bottom, x, table_top)
    ys = [table_top, hy0]+[hy0-(r+1)*data_row_h for r in range(n_rows)]
    for y in ys:
        c.line(ox, y, ox+table_w, y)

draw_amp_table(margin, 'inverting', "反転増幅　Av = \u2212R2/R1")
draw_amp_table(margin+table_w+10*mm, 'noninverting', "非反転増幅　Av = 1+R2/R1")

c.showPage()
c.save()
print("saved")
