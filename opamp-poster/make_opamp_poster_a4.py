# -*- coding: utf-8 -*-
import json, os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader

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
BORDER_WIDTH = 1.0

CIRCUIT_IMAGE_PATH = './opamp_circuit_uploaded.png'  # placeholder path for the user's image

def fit_font(text, max_w, max_h, start=40, min_size=4.0):
    size = min(start, max_h)
    while size > min_size and pdfmetrics.stringWidth(text, 'IPAGothic', size) > max_w:
        size -= 0.15
    return size

def fmt(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:g}"

page_w, page_h = landscape(A4)
c = canvas.Canvas('./opamp_poster_a4.pdf', pagesize=landscape(A4))
margin = 8*mm
gap = 5*mm

c.setFillColor(COL_BG)
c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

col_w = (page_w - 2*margin - 2*gap) / 3
col1_x = margin
col2_x = margin + col_w + gap
col3_x = margin + 2*(col_w + gap)
content_top = page_h - margin
content_bottom = margin

# ============================================================
# Column 1: title + circuit(s) + scaling explanation
# ============================================================
y = content_top
c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 11)
c.drawString(col1_x, y-5*mm, "オペアンプ増幅回路")
c.setFont('IPAGothic', 11)
c.drawString(col1_x, y-10.5*mm, "抵抗値早見表")
c.setFont('IPAGothic', 6.3)
c.setFillColor(COL_MUTED)
c.drawString(col1_x, y-15*mm, "Zin(=R1)を39/51/100/200に固定")
c.drawString(col1_x, y-18.5*mm, "枠線=系列／E48は下線／[E24代替]併記")

y_img_top = y - 22*mm

if os.path.exists(CIRCUIT_IMAGE_PATH):
    img = ImageReader(CIRCUIT_IMAGE_PATH)
    iw, ih = img.getSize()
    disp_w = col_w
    disp_h = disp_w * ih / iw
    max_h = 60*mm
    if disp_h > max_h:
        disp_h = max_h
        disp_w = disp_h * iw / ih
    c.drawImage(img, col1_x, y_img_top-disp_h, width=disp_w, height=disp_h,
                preserveAspectRatio=True, mask='auto')
    y_after_circuit = y_img_top - disp_h - 4*mm
else:
    ph_h = 40*mm
    c.setFillColor(COL_BOX)
    c.rect(col1_x, y_img_top-ph_h, col_w, ph_h, fill=1, stroke=0)
    c.setStrokeColor(COL_GRID)
    c.setLineWidth(0.5)
    c.rect(col1_x, y_img_top-ph_h, col_w, ph_h, fill=0, stroke=1)
    c.setFillColor(COL_MUTED)
    c.setFont('IPAGothic', 7)
    c.drawCentredString(col1_x+col_w/2, y_img_top-ph_h/2+3*mm, "回路図画像 未アップロード")
    c.setFont('IPAGothic', 6)
    c.drawCentredString(col1_x+col_w/2, y_img_top-ph_h/2-2*mm, "(チャットに画像を添付してください)")
    y_after_circuit = y_img_top - ph_h - 4*mm

box_h = 60*mm
box_top = y_after_circuit
c.setFillColor(COL_BOX)
c.rect(col1_x, box_top-box_h, col_w, box_h, fill=1, stroke=0)
c.setStrokeColor(COL_GRID)
c.setLineWidth(0.5)
c.rect(col1_x, box_top-box_h, col_w, box_h, fill=0, stroke=1)

c.setFillColor(COL_TEXT)
c.setFont('IPAGothic', 7.5)
c.drawString(col1_x+2*mm, box_top-4.5*mm, "\u25c6 \u00d710\u207f スケーリングの使い方")

c.setFont('IPAGothic', 6.0)
tx = col1_x+2*mm
lines1 = [
    "① Avは変えず入力インピーダンス",
    "だけ変えたい → R1・R2を両方",
    "×10ⁿすればよい（比R2/R1は不変）",
    "例：Zin=100・Av=10(R2=1000)を",
    "Zin=10kΩにしたい→R1=1000,",
    "R2=10000に置き換える（×10）",
]
yy = box_top-9*mm
for l in lines1:
    c.setFillColor(COL_TEXT)
    c.drawString(tx, yy, l)
    yy -= 3.1*mm

yy -= 1.3*mm
lines2 = [
    "② Av自体を変えたい → 比R2/R1が",
    "変わるので×10ⁿでは済まない、",
    "表の別のAv行を参照する",
    "例：Av=10→100にしたいなら",
    "「Av=10の行を10倍」ではなく",
    "「Av=100の行」を新たに参照",
]
for l in lines2:
    c.setFillColor(COL_TEXT)
    c.drawString(tx, yy, l)
    yy -= 3.1*mm

yy -= 1.3*mm
c.setFillColor(COL_MUTED)
c.drawString(tx, yy, "「桁」と「比率」は独立：桁は掛け算、"); yy -= 3.1*mm
c.drawString(tx, yy, "ゲインは表を引き直す必要がある")

legend_y = box_top - box_h - 6*mm
c.setFont('IPAGothic', 6.5)
legend_defs = [("E12", BORDER_E12, False), ("E24", BORDER_E24, False), ("E48", BORDER_E48, True)]
lx = col1_x
line_len = 4*mm
for i, (label, col, underline) in enumerate(legend_defs):
    x0 = lx
    c.setStrokeColor(col)
    c.setLineWidth(1.8)
    c.line(x0, legend_y, x0+line_len, legend_y)
    if underline:
        c.setStrokeColor(black)
        c.setLineWidth(0.8)
        c.line(x0, legend_y-1*mm, x0+line_len, legend_y-1*mm)
    c.setFillColor(COL_TEXT)
    c.drawString(x0+line_len+1.5*mm, legend_y-1*mm, label)
    lx += 20*mm

# ============================================================
# Tables (columns 2 and 3)
# ============================================================
table_top = content_top - 5*mm
table_bottom = content_bottom
header_row_h = 7*mm
label_col_w = 9*mm
n_data_cols = len(R1_options)
n_rows = len(gains)

def draw_amp_table(ox, kind_key, title):
    c.setFont('IPAGothic', 8.5)
    c.setFillColor(COL_TEXT)
    c.drawString(ox, table_top+2.5*mm, title)

    data_col_w = (col_w - label_col_w) / n_data_cols
    data_row_h = (table_top - header_row_h - table_bottom) / n_rows

    hy0 = table_top - header_row_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(ox, hy0, label_col_w, header_row_h, fill=1, stroke=0)
    c.setFillColor(COL_TEXT)
    txt = "Av"
    fsize = fit_font(txt, label_col_w-1*mm, header_row_h-1.5*mm, start=9)
    c.setFont('IPAGothic', fsize)
    c.drawCentredString(ox+label_col_w/2, hy0+header_row_h/2-fsize*0.32, txt)

    for i, R1 in enumerate(R1_options):
        x0 = ox+label_col_w+i*data_col_w
        c.setFillColor(COL_HEADER_BG)
        c.rect(x0, hy0, data_col_w, header_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        lbl = f"{R1}"
        fsize = fit_font(lbl, data_col_w-1*mm, header_row_h-1.5*mm, start=9)
        c.setFont('IPAGothic', fsize)
        c.drawCentredString(x0+data_col_w/2, hy0+header_row_h/2-fsize*0.32, lbl)

    for r, g in enumerate(gains):
        ry0 = hy0-(r+1)*data_row_h
        c.setFillColor(COL_HEADER_BG)
        c.rect(ox, ry0, label_col_w, data_row_h, fill=1, stroke=0)
        c.setFillColor(COL_TEXT)
        lbl = fmt(g)
        fsize = fit_font(lbl, label_col_w-1*mm, data_row_h-1.5*mm, start=11)
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
                txt = "buf"
                fsize = fit_font(txt, data_col_w-1*mm, data_row_h-1.5*mm, start=9)
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
            max_w = data_col_w - 1*mm
            top_h = data_row_h*(0.55 if has_alt else 0.85)
            fsize = fit_font(main_text, max_w, top_h, start=10)
            c.setFont('IPAGothic', fsize)
            ty = ry0 + data_row_h - fsize*0.95 if has_alt else ry0+data_row_h/2-fsize*0.28
            c.drawCentredString(x0+data_col_w/2, ty, main_text)
            if cell['src'] == 'E48' and not has_alt:
                tw2 = pdfmetrics.stringWidth(main_text, 'IPAGothic', fsize)
                ux0 = x0+data_col_w/2-tw2/2; ux1 = x0+data_col_w/2+tw2/2
                uy = ty - fsize*0.10
                c.setStrokeColor(black); c.setLineWidth(max(0.5, fsize*0.04))
                c.line(ux0, uy, ux1, uy)

            if not has_alt:
                gain_text = f"実{cell['gain']:g}"
                gfsize = fit_font(gain_text, max_w, 3*mm, start=4.3)
                c.setFont('IPAGothic', gfsize)
                c.setFillColor(COL_MUTED)
                c.drawCentredString(x0+data_col_w/2, ry0+0.8*mm, gain_text)
            else:
                alt = cell['alt24']
                c.setStrokeColor(BORDER_E24)
                c.setLineWidth(0.5)
                c.line(x0+0.8*mm, ry0+data_row_h*0.42, x0+data_col_w-0.8*mm, ry0+data_row_h*0.42)
                alt_text = f"E24:{fmt(alt['r2'])}"
                afsize = fit_font(alt_text, max_w, 3*mm, start=4.3)
                c.setFont('IPAGothic', afsize)
                c.setFillColor(BORDER_E24)
                c.drawCentredString(x0+data_col_w/2, ry0+data_row_h*0.20, alt_text)
                gtext = f"実{alt['gain']:g}"
                c.drawCentredString(x0+data_col_w/2, ry0+0.6*mm, gtext)

    c.setStrokeColor(COL_GRID)
    c.setLineWidth(0.3)
    xs = [ox, ox+label_col_w]+[ox+label_col_w+i*data_col_w for i in range(1, n_data_cols+1)]
    for x in xs:
        c.line(x, table_bottom, x, table_top)
    ys = [table_top, hy0]+[hy0-(r+1)*data_row_h for r in range(n_rows)]
    for yv in ys:
        c.line(ox, yv, ox+col_w, yv)

draw_amp_table(col2_x, 'inverting', "反転増幅　Av=\u2212R2/R1")
draw_amp_table(col3_x, 'noninverting', "非反転増幅　Av=1+R2/R1")

c.showPage()
c.save()
print("saved")
