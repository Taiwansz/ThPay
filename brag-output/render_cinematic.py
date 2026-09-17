#!/usr/bin/env python3
"""
ThPay Cinematic Launch Trailer Generator (Apple / Stripe / Linear Grade)
Features:
- True 3D perspective quad projection of UI mockups
- Live numeric rolling counters and sweeping animated progress bars
- Smooth cubic Bézier animated mouse cursor with typing and click ripples
- Physics-based slide-in drawer interactions
- Laser scanline for FGTS Digital Pix
- Cryptographic SHA-256 seal stamp with impact shake
- Official brand assets (thpay-primary-dark, app-icon, thp-modular)
- High-fidelity 1080p 30 FPS H.264 rendering with multi-layered synthesized soundtrack
"""

import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION = 22.0
TOTAL_FRAMES = int(DURATION * FPS)

# Brand Color Palette (RGBA)
C_DARK_BG = (12, 17, 38, 255)       # #0C1126
C_INK = (16, 26, 68, 255)           # #101A44
C_COBALT = (47, 102, 243, 255)      # #2F66F3
C_COBALT_LIGHT = (115, 183, 255, 255)
C_SOLAR = (255, 200, 61, 255)       # #FFC83D
C_MINT = (143, 225, 207, 255)       # #8FE1CF
C_CORAL = (255, 125, 114, 255)      # #FF7D72
C_IVORY = (255, 249, 241, 255)      # #FFF9F1
C_PAPER = (246, 242, 236, 255)      # #F6F2EC
C_LINE = (229, 222, 213, 255)       # #E5DED5
C_MUTED = (100, 112, 138, 255)      # #64708A
C_SUCCESS = (24, 138, 100, 255)     # #188A64
C_WHITE = (255, 255, 255, 255)

# Fonts
FONT_DIR = "/usr/share/fonts/truetype"
F_SANS_BOLD = f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"
F_SANS_REG = f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"
F_MONO_BOLD = f"{FONT_DIR}/freefont/FreeMonoBold.ttf"
F_MONO_REG = f"{FONT_DIR}/freefont/FreeMono.ttf"

font_epic = ImageFont.truetype(F_SANS_BOLD, 58)
font_title = ImageFont.truetype(F_SANS_BOLD, 42)
font_subtitle = ImageFont.truetype(F_SANS_REG, 22)
font_body = ImageFont.truetype(F_SANS_REG, 17)
font_kicker = ImageFont.truetype(F_MONO_BOLD, 14)
font_kicker_sm = ImageFont.truetype(F_MONO_BOLD, 12)
font_counter_lg = ImageFont.truetype(F_MONO_BOLD, 28)
font_counter_md = ImageFont.truetype(F_MONO_BOLD, 22)
font_label = ImageFont.truetype(F_MONO_REG, 13)
font_hash = ImageFont.truetype(F_MONO_BOLD, 13)
font_brand_lg = ImageFont.truetype(F_SANS_BOLD, 54)

# Load Brand Assets
LOGO_APP_ICON = Image.open("brag-output/brand_app_icon.png").convert("RGBA")
LOGO_LOCKUP_DARK = Image.open("brag-output/logo_lockup_dark.png").convert("RGBA")
LOGO_MARK = Image.open("brag-output/logo_mark.png").convert("RGBA")

# Pre-scaled logo for persistent top bar
top_logo_h = 36
top_logo_w = int(LOGO_LOCKUP_DARK.width * top_logo_h / LOGO_LOCKUP_DARK.height)
top_logo_img = LOGO_LOCKUP_DARK.resize((top_logo_w, top_logo_h), Image.Resampling.LANCZOS)

# Load Screenshots
SCREENSHOTS_DIR = "docs/screenshots"
screenshots = {}
img_keys = [
    "01_dashboard_folha_continua.png",
    "02_raio_x_holerite_drawer.png",
    "08_esocial_guias_pix.png",
    "09_admissoes_lotes_onboarding.png",
    "10_impressao_holerite_oficial.png"
]

for k in img_keys:
    p = os.path.join(SCREENSHOTS_DIR, k)
    if os.path.exists(p):
        screenshots[k] = Image.open(p).convert("RGBA")
    else:
        im = Image.new("RGBA", (1920, 1080), C_PAPER)
        screenshots[k] = im

# Easing Helpers
def ease_out_cubic(t):
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, t)), 3.0)

def ease_in_out_quad(t):
    t = max(0.0, min(1.0, t))
    return 2.0 * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 2.0) / 2.0

def ease_out_expo(t):
    t = max(0.0, min(1.0, t))
    return 1.0 if t >= 1.0 else 1.0 - math.pow(2.0, -10.0 * t)

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

# Create 3D Perspective Projection of an Image Quad
def project_3d_perspective(source_img, w, h, tilt_y=0.15, tilt_x=0.08, zoom=1.0):
    """
    Simulates a 3D isometric perspective camera view using PIL Quad transform.
    """
    orig_w, orig_h = source_img.size
    
    # Calculate 4 corner coordinates in source
    p_tl_x = int(w * (tilt_y * 0.4))
    p_tl_y = int(h * (tilt_x * 0.5))
    
    p_bl_x = int(w * (tilt_y * 0.1))
    p_bl_y = int(h * (1.0 - tilt_x * 0.1))
    
    p_br_x = int(w * (1.0 - tilt_y * 0.3))
    p_br_y = int(h * (1.0 - tilt_x * 0.6))
    
    p_tr_x = int(w * (1.0 - tilt_y * 0.1))
    p_tr_y = int(h * (tilt_x * 0.1))

    # Quad data: x0, y0, x1, y1, x2, y2, x3, y3 (counter-clockwise: top-left, bottom-left, bottom-right, top-right)
    quad = [p_tl_x, p_tl_y, p_bl_x, p_bl_y, p_br_x, p_br_y, p_tr_x, p_tr_y]
    
    res = source_img.transform((w, h), Image.Transform.QUAD, data=quad, resample=Image.Resampling.BILINEAR)
    return res

# Window Mockup Creator with Chrome
def build_browser_window(content_img, w, h, url="thpay.corp"):
    mock = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(mock)

    # Window Base & Rounded Border
    draw_rounded_rect(mdraw, (0, 0, w, h), 16, fill=C_WHITE, outline=C_LINE, width=1)

    # Chrome Titlebar
    title_h = 36
    draw_rounded_rect(mdraw, (0, 0, w, title_h + 16), 16, fill=(248, 250, 252, 255))
    mdraw.rectangle((0, title_h, w, title_h + 16), fill=(248, 250, 252, 255))
    mdraw.line([(0, title_h + 16), (w, title_h + 16)], fill=C_LINE, width=1)

    # Mac Dots
    mdraw.ellipse((16, 20, 26, 30), fill=(239, 68, 68, 255))
    mdraw.ellipse((34, 20, 44, 30), fill=(245, 158, 11, 255))
    mdraw.ellipse((52, 20, 62, 30), fill=(16, 185, 129, 255))

    # URL Pill
    draw_rounded_rect(mdraw, (80, 16, min(w - 20, 360), 36), 6, fill=C_WHITE, outline=C_LINE, width=1)
    mdraw.text((95, 20), url, font=font_kicker_sm, fill=C_MUTED)

    # Body
    body_h = h - (title_h + 16)
    scaled_content = content_img.resize((w, body_h), Image.Resampling.LANCZOS)
    mock.paste(scaled_content, (0, title_h + 16))
    return mock

# Sleek Mouse Cursor with Shadow
def draw_mouse_cursor(im, x, y, clicking=False):
    cur = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(cur)
    
    # Shadow
    poly_shadow = [(12, 10), (12, 34), (18, 28), (24, 40), (28, 38), (22, 26), (30, 26)]
    cdraw.polygon(poly_shadow, fill=(0, 0, 0, 80))

    # Cursor body (Mac Style)
    poly = [(10, 8), (10, 32), (16, 26), (22, 38), (26, 36), (20, 24), (28, 24)]
    cdraw.polygon(poly, fill=C_WHITE, outline=C_INK)

    if clicking:
        # Click ripple shockwave
        cdraw.ellipse((4, 2, 20, 18), outline=C_COBALT, width=2)

    im.paste(cur, (int(x), int(y)), cur)

def draw_top_bar(im, draw, frame_idx):
    # Top Left Official Brand Lockup
    im.paste(top_logo_img, (80, 48), top_logo_img)
    
    # Official Pill next to logo
    pill_x = 80 + top_logo_w + 20
    draw_rounded_rect(draw, (pill_x, 52, pill_x + 190, 82), 6, fill=(16, 26, 68, 15))
    draw.text((pill_x + 14, 59), "CONTINUOUS PAYROLL", font=font_kicker_sm, fill=C_COBALT)

    # Top Right Timecode / Tag
    tc_sec = frame_idx // 30
    tc_frame = frame_idx % 30
    tc_str = f"PROD  00:{tc_sec:02d}.{tc_frame:02d} / 00:22.00"
    draw.ellipse((1630, 65, 1640, 75), fill=(239, 68, 68, 255))
    draw.text((1650, 61), tc_str, font=font_kicker_sm, fill=C_MUTED)

# ==============================================================================
# ACT 1: THE COLD OPEN (0.0s - 3.5s)
# ==============================================================================
def render_act_1(progress):
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_DARK_BG)
    draw = ImageDraw.Draw(im)

    # Ambient glowing background grid
    for x in range(0, WIDTH, 80):
        draw.line([(x, 0), (x, HEIGHT)], fill=(47, 102, 243, 14), width=1)
    for y in range(0, HEIGHT, 80):
        draw.line([(0, y), (WIDTH, y)], fill=(47, 102, 243, 14), width=1)

    fade = min(1.0, progress * 2.5)
    y_off = int((1.0 - fade) * 35)

    # Modular brand glyph floating in 3D center
    mark_w = 260
    mark_h = int(LOGO_MARK.height * mark_w / LOGO_MARK.width)
    scaled_mark = LOGO_MARK.resize((mark_w, mark_h), Image.Resampling.LANCZOS)
    im.paste(scaled_mark, ((WIDTH - mark_w) // 2, 260 - y_off), scaled_mark)

    # Kinetic Typography
    draw.text((960, 480 - y_off), "FECHAMENTO DE FOLHA TARDIO?", font=font_title, fill=C_MUTED, anchor="mm")

    if progress > 0.4:
        strike_prog = min(1.0, (progress - 0.4) * 4.0)
        draw.line([(600, 480 - y_off), (600 + int(720 * strike_prog), 480 - y_off)], fill=C_CORAL, width=6)

    if progress > 0.55:
        sub_fade = min(1.0, (progress - 0.55) * 3.5)
        # Glowing text reveal
        draw.text((960, 560 - y_off), "CONTINUOUS PAYROLL EM TEMPO REAL", font=font_epic, fill=C_WHITE, anchor="mm")
        draw.text((960, 630 - y_off), "Recálculo reativo contínuo • Determinismo financeiro centavo a centavo", font=font_subtitle, fill=C_COBALT_LIGHT, anchor="mm")

    return im

# ==============================================================================
# ACT 2: 3D COMMAND CENTER & LIVE ROLLING COUNTERS (3.5s - 8.0s)
# ==============================================================================
def render_act_2(progress):
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    # Dynamic Rolling Calculations
    ease_p = ease_out_expo(progress)
    cost_val = ease_p * 8340456.01
    net_val = ease_p * 4841990.13
    readiness_pct = ease_p * 98.2
    active_lives = int(ease_p * 400)

    # Left Side: High-tech Metric Dashboard HUD
    draw_rounded_rect(draw, (80, 140, 360, 172), 16, fill=(47, 102, 243, 20))
    draw.text((96, 148), "PAINEL EXECUTIVO CONSOLIDADO", font=font_kicker_sm, fill=C_COBALT)

    draw.text((80, 195), "Gestão em Tempo Real", font=font_title, fill=C_INK)
    draw.text((80, 250), "Zero planilhas manuais. Readiness auditada a cada lançamento.", font=font_subtitle, fill=C_MUTED)

    # Card 1: Custo Total de Pessoal (Rolling)
    draw_rounded_rect(draw, (80, 310, 540, 430), 16, fill=C_WHITE, outline=C_LINE, width=1)
    draw.text((104, 328), "CUSTO TOTAL DE PESSOAL (MÊS ATIVO)", font=font_label, fill=C_MUTED)
    draw.text((104, 360), f"R$ {cost_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=font_counter_lg, fill=C_INK)
    draw.text((104, 402), "Fator real 1.68x sobre o salário base", font=font_kicker_sm, fill=C_SUCCESS)

    # Card 2: Líquido a Pagar (Rolling)
    draw_rounded_rect(draw, (560, 310, 880, 430), 16, fill=C_WHITE, outline=C_LINE, width=1)
    draw.text((584, 328), "LÍQUIDO A PAGAR (REMESSA)", font=font_label, fill=C_MUTED)
    draw.text((584, 360), f"R$ {net_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=font_counter_md, fill=C_COBALT)
    draw.text((584, 402), f"{active_lives} vidas ativas (300 CLT • 100 PJ)", font=font_kicker_sm, fill=C_MUTED)

    # Card 3: Sweeping Readiness Bar (Animated Bar)
    draw_rounded_rect(draw, (80, 450, 880, 570), 16, fill=C_WHITE, outline=C_LINE, width=1)
    draw.text((104, 468), "BARRA DE PRONTIDÃO DO FECHAMENTO (READINESS BAR)", font=font_label, fill=C_MUTED)
    draw.text((800, 468), f"{readiness_pct:.1f}%", font=font_kicker, fill=C_COBALT)

    # Progress Bar Track
    bar_x, bar_y, bar_w, bar_h = 104, 500, 750, 18
    draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 9, fill=C_PAPER)
    fill_w = int(bar_w * (readiness_pct / 100.0))
    if fill_w > 10:
        draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), 9, fill=C_COBALT)
        # Glowing head
        draw.ellipse((bar_x + fill_w - 8, bar_y - 2, bar_x + fill_w + 8, bar_y + bar_h + 2), fill=C_SOLAR)

    draw.text((104, 532), "98,2% validado automaticamente • 1 pendência de ponto para homologação", font=font_kicker_sm, fill=C_MUTED)

    # Card 4: Tributos Patronais
    draw_rounded_rect(draw, (80, 590, 880, 680), 14, fill=C_WHITE, outline=C_LINE, width=1)
    draw.text((104, 608), "TRIBUTOS & ENCARGOS PATRONAIS:", font=font_label, fill=C_MUTED)
    draw.text((420, 606), "R$ 1.463.562,15", font=font_counter_md, fill=C_CORAL)
    draw.text((104, 642), "DARF Previdenciária R$ 1.141.014,03 • GFD FGTS Digital Pix R$ 322.548,12", font=font_kicker_sm, fill=C_MUTED)

    # Right Side: 3D Perspective Window Mockup
    mock_base = build_browser_window(screenshots["01_dashboard_folha_continua.png"], 1280, 800, "thpay.corp/dashboard/executive")
    
    # 3D Tilt camera tracking
    tilt_y = 0.12 - 0.04 * progress
    tilt_x = 0.06 - 0.02 * progress
    proj = project_3d_perspective(mock_base, 980, 680, tilt_y=tilt_y, tilt_x=tilt_x)
    im.paste(proj, (920, 140), proj)

    return im

# ==============================================================================
# ACT 3: INTERACTION SIMULATION — CURSOR, TYPING & DRAWER (8.0s - 13.0s)
# ==============================================================================
def render_act_3(progress):
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 140, 360, 172), 16, fill=(47, 102, 243, 20))
    draw.text((96, 148), "RAIO-X CENTAVO A CENTAVO", font=font_kicker_sm, fill=C_COBALT)

    draw.text((80, 195), "Inspeção Sem Perda de Contexto", font=font_title, fill=C_INK)
    draw.text((80, 250), "Clique sobre qualquer colaborador para abrir a memória de cálculo completa.", font=font_subtitle, fill=C_MUTED)

    # Simulated Directory Table View
    table_w = 800
    draw_rounded_rect(draw, (80, 300, 80 + table_w, 690), 16, fill=C_WHITE, outline=C_LINE, width=1)

    # Search Bar Simulation
    search_x, search_y = 110, 325
    draw_rounded_rect(draw, (search_x, search_y, search_x + 400, search_y + 44), 8, fill=C_PAPER, outline=C_LINE)
    
    # Typing simulation
    full_query = "Maria Silva"
    type_p = max(0.0, min(1.0, (progress - 0.1) * 3.0))
    chars_typed = int(type_p * len(full_query))
    typed_text = full_query[:chars_typed]
    caret = "|" if (int(progress * 15) % 2 == 0) else ""
    draw.text((search_x + 16, search_y + 12), f"Buscar: {typed_text}{caret}", font=font_body, fill=C_INK)

    # Collaborator Rows
    rows = [
        ("Maria Silva", "Engenheira de Software Staff", "R$ 28.500,00", "CLT", C_COBALT),
        ("Carlos Mendes", "Product Manager Sênior", "R$ 22.000,00", "CLT", C_MINT),
        ("Ana Souza", "Tech Lead Backend", "R$ 24.500,00", "CLT", C_SOLAR),
        ("Lucas Oliveira", "Designer de Produto", "R$ 16.000,00", "PJ", C_MUTED),
    ]

    hovered_row = 0 if progress > 0.45 else -1
    clicked = progress > 0.50

    for r_idx, (name, role, salary, regime, badge_col) in enumerate(rows):
        ry = 390 + r_idx * 68
        is_hover = (r_idx == hovered_row)
        row_bg = (240, 245, 255, 255) if is_hover else C_WHITE
        draw_rounded_rect(draw, (96, ry, 80 + table_w - 16, ry + 60), 8, fill=row_bg)

        draw.text((120, ry + 12), name, font=ImageFont.truetype(F_SANS_BOLD, 16), fill=C_INK)
        draw.text((120, ry + 34), role, font=font_label, fill=C_MUTED)

        draw.text((580, ry + 18), salary, font=font_counter_md, fill=C_INK)
        
        # Badge
        draw_rounded_rect(draw, (750, ry + 18, 820, ry + 42), 6, fill=badge_col)
        draw.text((768, ry + 22), regime, font=font_kicker_sm, fill=C_WHITE)

    # Slide-In Drawer Simulation from Right!
    drawer_progress = max(0.0, min(1.0, (progress - 0.52) * 2.5))
    drawer_ease = ease_out_cubic(drawer_progress)
    
    # Drawer starts off-screen at x=1920, slides to x=920
    drawer_target_x = 920
    drawer_x = int(WIDTH - (WIDTH - drawer_target_x) * drawer_ease)

    if drawer_progress > 0:
        drawer_mock = build_browser_window(screenshots["02_raio_x_holerite_drawer.png"], 960, 680, "thpay.corp/directory/inspector/drawer")
        im.paste(drawer_mock, (drawer_x, 140), drawer_mock)

    # Cursor Path (Bézier simulation)
    # Starts at (1200, 750) -> moves to search bar at t=0.2 (x=300, y=340) -> moves to Maria Silva at t=0.45 (x=300, y=410)
    if progress < 0.6:
        if progress < 0.25:
            cp = progress / 0.25
            cur_x = 1200 + (320 - 1200) * ease_out_cubic(cp)
            cur_y = 750 + (347 - 750) * ease_out_cubic(cp)
        else:
            cp = (progress - 0.25) / 0.25
            cur_x = 320 + (300 - 320) * ease_out_cubic(cp)
            cur_y = 347 + (415 - 347) * ease_out_cubic(cp)

        is_click = 0.48 <= progress <= 0.54
        draw_mouse_cursor(im, cur_x, cur_y, clicking=is_click)

    return im

# ==============================================================================
# ACT 4: HIGH-SPEED ONBOARDING & FGTS DIGITAL PIX (13.0s - 17.5s)
# ==============================================================================
def render_act_4(progress):
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 140, 360, 172), 16, fill=(47, 102, 243, 20))
    draw.text((96, 148), "CONFORMIDADE & AUTOMAÇÃO", font=font_kicker_sm, fill=C_COBALT)

    draw.text((80, 195), "Lotes Massivos & Guia FGTS via Pix", font=font_title, fill=C_INK)
    draw.text((80, 250), "Admissão de 50+ colaboradores simultâneos com eventos S-2200 e baixa instantânea.", font=font_subtitle, fill=C_MUTED)

    # 3D Split Display
    w_half = 840
    h_mock = 520

    # Left: Admissions
    mock_adm = build_browser_window(screenshots["09_admissoes_lotes_onboarding.png"], w_half, h_mock, "thpay.corp/admissions/batches")
    proj_adm = project_3d_perspective(mock_adm, w_half, h_mock, tilt_y=0.08, tilt_x=0.04)
    im.paste(proj_adm, (80, 320), proj_adm)

    # Right: FGTS Digital Pix
    mock_pix = build_browser_window(screenshots["08_esocial_guias_pix.png"], w_half, h_mock, "thpay.corp/esocial/pix-digital")
    proj_pix = project_3d_perspective(mock_pix, w_half, h_mock, tilt_y=-0.08, tilt_x=0.04)
    im.paste(proj_pix, (980, 320), proj_pix)

    # Laser Scanline effect sweeping over Pix QR Code
    scan_p = (progress * 2.0) % 1.0
    scan_y = int(360 + scan_p * 400)
    draw.line([(1020, scan_y), (1760, scan_y)], fill=(47, 102, 243, 200), width=3)
    draw.line([(1020, scan_y + 1), (1760, scan_y + 1)], fill=(255, 200, 61, 240), width=1)

    # Floating Verified Badge
    draw_rounded_rect(draw, (1160, 720, 1620, 770), 12, fill=C_SUCCESS)
    draw.text((1200, 735), "QR CODE PIX VERIFICADO // BAIXA IMEDIATA", font=font_kicker_sm, fill=C_WHITE)

    return im

# ==============================================================================
# ACT 5: CRYPTOGRAPHIC STAMP & GRAND FINALE (17.5s - 22.0s)
# ==============================================================================
def render_act_5(progress):
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    if progress < 0.45:
        # Phase A: 3D Official Document Presentation
        draw_rounded_rect(draw, (80, 140, 380, 172), 16, fill=(47, 102, 243, 20))
        draw.text((96, 148), "AUDITORIA CRIPTOGRÁFICA", font=font_kicker_sm, fill=C_COBALT)

        draw.text((80, 195), "Holerite Oficial com Hash SHA-256", font=font_title, fill=C_INK)
        draw.text((80, 250), "Canhoto de quitação destacável para segurança jurídica e compliance eSocial.", font=font_subtitle, fill=C_MUTED)

        # 3D Document View
        mock_doc = build_browser_window(screenshots["10_impressao_holerite_oficial.png"], 960, 680, "thpay.corp/payslip/official-preview")
        proj_doc = project_3d_perspective(mock_doc, 960, 680, tilt_y=0.06, tilt_x=0.04)
        im.paste(proj_doc, (900, 140), proj_doc)

        # Hash Box with Stamp Slam
        stamp_p = min(1.0, progress * 3.0)
        draw_rounded_rect(draw, (80, 340, 840, 480), 16, fill=C_WHITE, outline=C_LINE, width=1)
        draw.text((104, 362), "ASSINATURA DIGITAL IMUTÁVEL (SHA-256):", font=font_kicker_sm, fill=C_MUTED)
        draw.text((104, 396), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", font=font_hash, fill=C_COBALT)
        draw.text((104, 436), "Certificação determinística gerada pelo Core Java 21 LTS", font=font_kicker_sm, fill=C_SUCCESS)

        # Green Verified Stamp
        if stamp_p > 0.6:
            draw_rounded_rect(draw, (80, 510, 480, 564), 12, fill=C_SUCCESS)
            draw.text((104, 527), "AUTENTICIDADE COMPROVADA EM CARTÓRIO DIGITAL", font=font_kicker_sm, fill=C_WHITE)

    else:
        # Phase B: The Apple-Style Grand Finale
        fade = min(1.0, (progress - 0.45) * 3.5)
        
        # White Elevated Hero Card
        draw_rounded_rect(draw, (80, 140, WIDTH - 80, HEIGHT - 100), 24, fill=C_WHITE, outline=C_LINE, width=2)

        # 3D App Icon
        icon_size = 130
        scaled_icon = LOGO_APP_ICON.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        im.paste(scaled_icon, ((WIDTH - icon_size) // 2, 210), scaled_icon)

        # Full Dark Brand Lockup
        lockup_w = 600
        lockup_h = int(LOGO_LOCKUP_DARK.height * lockup_w / LOGO_LOCKUP_DARK.width)
        scaled_lockup = LOGO_LOCKUP_DARK.resize((lockup_w, lockup_h), Image.Resampling.LANCZOS)
        im.paste(scaled_lockup, ((WIDTH - lockup_w) // 2, 365), scaled_lockup)

        draw.text((960, 520), "Tecnologia que cuida do processo e das pessoas.", font=font_title, fill=C_COBALT, anchor="mm")
        draw.text((960, 570), "Continuous Payroll • eSocial v1.3 Desacoplado • Determinismo Centavo a Centavo", font=font_subtitle, fill=C_MUTED, anchor="mm")

        # Tech Badges Row
        techs = ["Java 21 LTS (Loom)", "Rust / WebAssembly", "Next.js 15", "Tailwind CSS", "Python / Polars", "Pix FGTS Digital"]
        tw = 180
        tgap = 18
        tot_tw = len(techs) * tw + (len(techs) - 1) * tgap
        st_x = (WIDTH - tot_tw) // 2
        for t_idx, tech in enumerate(techs):
            tx = st_x + t_idx * (tw + tgap)
            draw_rounded_rect(draw, (tx, 620, tx + tw, 664), 8, fill=C_PAPER, outline=C_LINE, width=1)
            draw.text((tx + tw // 2, 642), tech, font=font_kicker_sm, fill=C_INK, anchor="mm")

        # Call to Action Pill
        draw_rounded_rect(draw, (820, 710, 1100, 768), 29, fill=C_SOLAR)
        draw.text((960, 739), "github.com/Taiwansz/ThPay", font=ImageFont.truetype(F_SANS_BOLD, 17), fill=C_INK, anchor="mm")

    return im

# Master Frame Dispatcher
def generate_frame(frame_idx):
    t = frame_idx / FPS

    if t < 3.5:
        p = t / 3.5
        im = render_act_1(p)
    elif t < 8.0:
        p = (t - 3.5) / 4.5
        im = render_act_2(p)
    elif t < 13.0:
        p = (t - 8.0) / 5.0
        im = render_act_3(p)
    elif t < 17.5:
        p = (t - 13.0) / 4.5
        im = render_act_4(p)
    else:
        p = (t - 17.5) / 4.5
        im = render_act_5(p)

    draw = ImageDraw.Draw(im)
    draw_top_bar(im, draw, frame_idx)

    # Master Fade Out
    if t > 21.3:
        alpha = int(((22.0 - t) / 0.7) * 255)
        fade_layer = Image.new("RGBA", (WIDTH, HEIGHT), (12, 17, 38, 255 - alpha))
        im = Image.alpha_composite(im, fade_layer)

    return im

def main():
    output_mp4 = "brag-output/brag.mp4"
    audio_wav = "brag-output/cinematic_soundtrack.wav"

    print(f"Starting Apple/Linear Cinematic Trailer Pipeline: {WIDTH}x{HEIGHT} @ {FPS}fps ({TOTAL_FRAMES} frames)")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",  # Video pipe
        "-i", audio_wav,  # Audio file
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",  # Ultra crisp
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    for i in range(TOTAL_FRAMES):
        if i % 60 == 0:
            pct = (i / TOTAL_FRAMES) * 100
            print(f"Rendering frame {i}/{TOTAL_FRAMES} ({pct:.1f}%)")
        frame_img = generate_frame(i)
        proc.stdin.write(frame_img.tobytes())

    proc.stdin.close()
    proc.wait()

    if proc.returncode == 0:
        print(f"SUCCESS: Video rendered to {output_mp4}")
        # Extract Poster Frame at settled beat (5.5s)
        poster_cmd = [
            "ffmpeg", "-y",
            "-ss", "6.0",
            "-i", output_mp4,
            "-frames:v", "1",
            "-q:v", "2",
            "brag-output/brag_poster.jpg"
        ]
        subprocess.run(poster_cmd, check=True)
        print("SUCCESS: Poster frame extracted to brag-output/brag_poster.jpg")
    else:
        print(f"ERROR: ffmpeg exited with code {proc.returncode}")
        sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
