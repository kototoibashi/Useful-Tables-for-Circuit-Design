# -*- coding: utf-8 -*-
import json
import math
import os
import argparse
from reportlab.lib.pagesizes import A2, A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, black, white

# Register Japanese font dynamically based on OS
font_paths = [
    '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
    'C:/Windows/Fonts/msgothic.ttc',
    'C:/Windows/Fonts/meiryo.ttc',
]
font_path = None
for p in font_paths:
    if os.path.exists(p):
        font_path = p
        break
if not font_path:
    raise FileNotFoundError("Could not find a Japanese gothic font (msgothic.ttc, meiryo.ttc, ipag.ttf)")
pdfmetrics.registerFont(TTFont('IPAGothic', font_path))

script_dir = os.path.dirname(os.path.abspath(__file__))

E6 = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]
DECADES = [-2, -1, 0]

def build_e6_pool():
    pool = []
    for d in DECADES:
        for r1 in E6:
            for r2 in E6:
                r2_scaled = r2 * (10 ** d)
                ratio = r2_scaled / (r1 + r2_scaled) * 100
                if 1.0 <= ratio <= 50.0:
                    scale = 10
                    r1_new = round(r1 * scale) * (10 ** abs(d))
                    r2_new = round(r2 * scale)
                    pool.append((ratio, r1_new, r2_new, d))
    
    # Deduplicate by ratio, keeping the one with the smallest values
    unique_ratios = {}
    for ratio, r1, r2, d in pool:
        key = round(ratio, 6)
        if key not in unique_ratios:
            unique_ratios[key] = []
        unique_ratios[key].append((r1, r2, d))
        
    final_list = []
    for key, combos in unique_ratios.items():
        # Tiebreaker: smallest of R1, R2
        combos_sorted = sorted(combos, key=lambda c: (min(c[0], c[1]), max(c[0], c[1])))
        r1, r2, d = combos_sorted[0]
        final_list.append({
            'ratio': key,
            'r1': r1,
            'r2': r2,
            'd': d
        })
        
    return sorted(final_list, key=lambda x: x['ratio'])

E6_DATA = build_e6_pool()

# Color Theme - Sleek Dark Cyberpunk
COL_BG        = HexColor('#0f172a') # Slate 900
COL_PANEL_BG  = HexColor('#1e293b') # Slate 800
COL_TEXT      = HexColor('#f8fafc') # Slate 50
COL_MUTED     = HexColor('#94a3b8') # Slate 400
COL_GRID      = HexColor('#334155') # Slate 700
COL_ACCENT    = HexColor('#06b6d4') # Cyan 500
COL_HIGHLIGHT = HexColor('#f59e0b') # Amber 500

LAYOUT_CONFIGS = {
    'A2': {
        'pagesize': landscape(A2),
        'margin': 16 * mm,
        'panel_gap': 8 * mm,
        'title_font_size': 18,
        'subtitle_font_size': 9.0,
        'panel_title_font_size': 10.5,
        'header_font_size': 8.5,
        'cell_font_size': 8.0,
        'label_col_w': 10 * mm,
        'ratio_col_w': 22 * mm,
        'r12_col_w': 28 * mm,
        'values_col_w': 40 * mm,
        'row_h': 14.5 * mm,
        'header_row_h': 10 * mm,
        'schematic_panel_w': 105 * mm,
        'footer_font_size': 8.0,
        'footer_y_offset': 6 * mm,
    },
    'A4': {
        'pagesize': landscape(A4),
        'margin': 10 * mm,
        'panel_gap': 5 * mm,
        'title_font_size': 12,
        'subtitle_font_size': 6.5,
        'panel_title_font_size': 7.5,
        'header_font_size': 6.0,
        'cell_font_size': 5.5,
        'label_col_w': 8 * mm,
        'ratio_col_w': 16 * mm,
        'r12_col_w': 20 * mm,
        'values_col_w': 28 * mm,
        'row_h': 10.2 * mm,
        'header_row_h': 7 * mm,
        'schematic_panel_w': 72 * mm,
        'footer_font_size': 5.5,
        'footer_y_offset': 5.2 * mm,
    }
}

def format_resistor(val):
    if val >= 1000000:
        if val % 1000000 == 0:
            return f"{val // 1000000} MΩ"
        else:
            return f"{val / 1000000:.1f} MΩ"
    elif val >= 1000:
        if val % 1000 == 0:
            return f"{val // 1000} kΩ"
        else:
            return f"{val / 1000:.1f} kΩ"
    else:
        return f"{val} Ω"

def draw_schematic(c, x, y, w, h, size):
    # Draw a bounding panel for the schematic
    c.setStrokeColor(COL_GRID)
    c.setLineWidth(1.0)
    c.setFillColor(COL_PANEL_BG)
    c.roundRect(x, y, w, h, 4*mm, fill=1, stroke=1)
    
    # Title
    c.setFillColor(COL_ACCENT)
    c.setFont('IPAGothic', 11 if size == 'A2' else 7.5)
    c.drawString(x + 8*mm, y + h - 10*mm, "分圧回路の基本構成")
    
    # Schematic lines
    c.setStrokeColor(COL_TEXT)
    c.setLineWidth(1.5 if size == 'A2' else 1.0)
    
    cx = x + w / 2 - 15*mm
    # Vin terminal and line down
    c.circle(cx, y + h - 25*mm, 2*mm, fill=0, stroke=1)
    c.setFillColor(COL_TEXT)
    c.setFont('IPAGothic', 9 if size == 'A2' else 6)
    c.drawString(cx - 10*mm, y + h - 26*mm, "Vin")
    c.line(cx, y + h - 27*mm, cx, y + h - 35*mm)
    
    # Resistor R1
    c.setFillColor(COL_PANEL_BG)
    c.rect(cx - 4*mm, y + h - 55*mm, 8*mm, 20*mm, fill=1, stroke=1)
    c.setFillColor(COL_TEXT)
    c.setFont('IPAGothic', 10 if size == 'A2' else 7)
    c.drawCentredString(cx, y + h - 47*mm, "R1")
    
    # Node connection
    c.line(cx, y + h - 55*mm, cx, y + h - 75*mm)
    # Vout branch
    c.line(cx, y + h - 65*mm, cx + 25*mm, y + h - 65*mm)
    c.circle(cx + 25*mm, y + h - 65*mm, 2*mm, fill=0, stroke=1)
    c.drawString(cx + 29*mm, y + h - 66*mm, "Vout")
    
    # Resistor R2
    c.setFillColor(COL_PANEL_BG)
    c.rect(cx - 4*mm, y + h - 95*mm, 8*mm, 20*mm, fill=1, stroke=1)
    c.setFillColor(COL_TEXT)
    c.drawCentredString(cx, y + h - 87*mm, "R2")
    
    # Ground connection
    c.line(cx, y + h - 95*mm, cx, y + h - 105*mm)
    # Ground symbol
    gy = y + h - 105*mm
    c.line(cx - 8*mm, gy, cx + 8*mm, gy)
    c.line(cx - 5*mm, gy - 2*mm, cx + 5*mm, gy - 2*mm)
    c.line(cx - 2*mm, gy - 4*mm, cx + 2*mm, gy - 4*mm)
    
    # Formulas on the right/bottom
    fy = y + h - 130*mm
    c.setFillColor(COL_TEXT)
    c.setFont('IPAGothic', 10 if size == 'A2' else 7)
    c.drawString(x + 8*mm, fy, "分圧公式:")
    c.setFont('IPAGothic', 12 if size == 'A2' else 8)
    c.setFillColor(COL_HIGHLIGHT)
    c.drawString(x + 12*mm, fy - 8*mm, "Vout = Vin * [ R2 / (R1 + R2) ]")
    
    c.setFillColor(COL_MUTED)
    c.setFont('IPAGothic', 8.5 if size == 'A2' else 6)
    notes = [
        "※ E6系列は入手性が最も良く、",
        "  手元の余り物でサクッと分圧回路を",
        "  組みたいときに最適です。",
        "※ 抵抗値は比率なので、同じ倍率",
        "  （10倍、100倍など）でスケールして",
        "  使用することができます。",
        "  例：2200 - 22 → 2.2kΩ - 22Ω",
        "      または 220kΩ - 2.2kΩ など",
    ]
    ny = fy - 22*mm
    for line in notes:
        c.drawString(x + 8*mm, ny, line)
        ny -= 5.5*mm if size == 'A2' else 4*mm

def generate_poster(size):
    cfg = LAYOUT_CONFIGS[size]
    page_w, page_h = cfg['pagesize']
    margin = cfg['margin']
    panel_gap = cfg['panel_gap']
    
    pdf_filename = f'voltage_divider_poster_e6_{size}.pdf'
    pdf_path = os.path.join(script_dir, pdf_filename)
    c = canvas.Canvas(pdf_path, pagesize=cfg['pagesize'])
    
    # Background
    c.setFillColor(COL_BG)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    
    # Title Block
    title_y = page_h - margin - 8*mm
    c.setFillColor(COL_TEXT)
    c.setFont('IPAGothic', cfg['title_font_size'])
    c.drawString(margin, title_y, "E6系列 2直列抵抗 分圧比 早見表 (1% 〜 50%)")
    c.setFont('IPAGothic', cfg['subtitle_font_size'])
    c.setFillColor(COL_MUTED)
    c.drawString(margin, title_y - (6*mm if size == 'A2' else 4.5*mm),
                 "Vout = Vin × R2/(R1+R2)  ｜  E6系列のみ（1.0, 1.5, 2.2, 3.3, 4.7, 6.8）で作れる全54通りの分圧比を網羅")
    
    # Calculate column dimensions
    grid_top = title_y - (14*mm if size == 'A2' else 10*mm)
    grid_bottom = margin + cfg['footer_y_offset'] + (4*mm if size == 'A2' else 2*mm)
    
    # Layout panels
    # We have 3 columns of data + 1 column for schematic
    available_w = page_w - 2*margin - 3*panel_gap
    data_columns_w = available_w - cfg['schematic_panel_w']
    col_w = data_columns_w / 3
    
    # Data splitting (54 items / 3 columns = 18 items per column)
    n_rows = 18
    col_data_w = cfg['label_col_w'] + cfg['ratio_col_w'] + cfg['r12_col_w'] + cfg['values_col_w']
    # Adjust column width to fit within panel width with slight margins
    
    for c_idx in range(3):
        cx_left = margin + c_idx * (col_w + panel_gap)
        cx_right = cx_left + col_w
        
        # Draw column panel background
        c.setFillColor(COL_PANEL_BG)
        c.setStrokeColor(COL_GRID)
        c.setLineWidth(1.0)
        c.roundRect(cx_left, grid_bottom, col_w, grid_top - grid_bottom, 4*mm, fill=1, stroke=1)
        
        # Panel Title
        start_idx = c_idx * n_rows
        end_idx = start_idx + n_rows - 1
        p_title = f"No.{start_idx+1:02d} 〜 No.{end_idx+1:02d} ({E6_DATA[start_idx]['ratio']:.2f}% 〜 {E6_DATA[end_idx]['ratio']:.2f}%)"
        
        c.setFillColor(COL_ACCENT)
        c.setFont('IPAGothic', cfg['panel_title_font_size'])
        c.drawString(cx_left + 6*mm, grid_top - 6*mm if size == 'A2' else grid_top - 4.5*mm, p_title)
        
        # Table Layout
        table_top = grid_top - (10*mm if size == 'A2' else 7.5*mm)
        row_h = (table_top - grid_bottom - cfg['header_row_h']) / n_rows
        
        # Draw Headers
        hy = table_top - cfg['header_row_h']
        c.setFillColor(COL_GRID)
        c.rect(cx_left + 4*mm, hy, col_w - 8*mm, cfg['header_row_h'], fill=1, stroke=0)
        
        c.setFillColor(COL_TEXT)
        c.setFont('IPAGothic', cfg['header_font_size'])
        
        # Header text alignment
        tx = cx_left + 4*mm
        # Widths
        w_lbl = cfg['label_col_w']
        w_rat = cfg['ratio_col_w']
        w_r12 = cfg['r12_col_w']
        w_val = col_w - 8*mm - w_lbl - w_rat - w_r12
        
        c.drawString(tx + 2*mm, hy + 2*mm if size == 'A2' else hy + 1.5*mm, "No.")
        c.drawString(tx + w_lbl + 2*mm, hy + 2*mm if size == 'A2' else hy + 1.5*mm, "分圧比")
        c.drawString(tx + w_lbl + w_rat + 2*mm, hy + 2*mm if size == 'A2' else hy + 1.5*mm, "R1 - R2 比率")
        c.drawString(tx + w_lbl + w_rat + w_r12 + 2*mm, hy + 2*mm if size == 'A2' else hy + 1.5*mm, "代表的な推奨抵抗値")
        
        # Draw Rows
        for r_idx in range(n_rows):
            item_idx = start_idx + r_idx
            item = E6_DATA[item_idx]
            
            ry = hy - (r_idx + 1) * row_h
            
            # Alternate row background
            if r_idx % 2 == 1:
                c.setFillColor(HexColor('#1e293b')) # Same as panel
            else:
                c.setFillColor(HexColor('#1b2535')) # Slightly darker slate
            
            c.rect(cx_left + 4*mm, ry, col_w - 8*mm, row_h, fill=1, stroke=0)
            
            # Print cell values
            c.setFont('IPAGothic', cfg['cell_font_size'])
            c.setFillColor(COL_MUTED)
            c.drawString(tx + 2*mm, ry + (row_h/2 - cfg['cell_font_size']*0.32), f"{item_idx+1:02d}")
            
            c.setFillColor(COL_HIGHLIGHT)
            c.setFont('IPAGothic', cfg['cell_font_size'] + 0.5)
            c.drawString(tx + w_lbl + 2*mm, ry + (row_h/2 - (cfg['cell_font_size']+0.5)*0.32), f"{item['ratio']:.4f}%")
            
            c.setFillColor(COL_TEXT)
            c.setFont('IPAGothic', cfg['cell_font_size'])
            c.drawString(tx + w_lbl + w_rat + 2*mm, ry + (row_h/2 - cfg['cell_font_size']*0.32), f"{item['r1']} - {item['r2']}")
            
            c.setFillColor(COL_ACCENT)
            r1_str = format_resistor(item['r1'])
            r2_str = format_resistor(item['r2'])
            c.drawString(tx + w_lbl + w_rat + w_r12 + 2*mm, ry + (row_h/2 - cfg['cell_font_size']*0.32), f"{r1_str} : {r2_str}")
            
            # Draw row border line
            c.setStrokeColor(HexColor('#334155'))
            c.setLineWidth(0.3)
            c.line(cx_left + 4*mm, ry, cx_right - 4*mm, ry)
            
    # Draw Schematic Panel on the right
    sx = margin + 3 * (col_w + panel_gap)
    draw_schematic(c, sx, grid_bottom, cfg['schematic_panel_w'], grid_top - grid_bottom, size)
    
    # Footer text
    foot_y = grid_bottom - cfg['footer_y_offset']
    c.setFillColor(COL_MUTED)
    c.setFont('IPAGothic', cfg['footer_font_size'])
    c.drawString(margin, foot_y, "※ 実際の回路では、抵抗器自身の許容誤差（E6系列は一般に±10%または±5%）によって出力電圧が変動するため注意してください。精密な分圧が必要な場合は、高精度なE24やE48系列をご使用ください。")
    
    c.showPage()
    c.save()
    print(f"[{size}] Saved {pdf_filename}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate E6 voltage divider posters in A2 and/or A4 landscape sizes.")
    parser.add_argument('--size', choices=['A2', 'A4', 'both'], default='both',
                        help="Paper size of the generated PDF (default: both)")
    args = parser.parse_args()
    
    if args.size == 'both':
        generate_poster('A2')
        generate_poster('A4')
    else:
        generate_poster(args.size)
