#!/usr/bin/env python3
"""
ThPay Launch Video Generator (/brag 100% Free Local Pipeline)
Renders a broadcast-quality 1080p 30 FPS MP4 video using Pillow + FFmpeg.
"""

import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION = 20.0
TOTAL_FRAMES = int(DURATION * FPS)

# Brand Colors (RGBA)
C_INK = (16, 26, 68, 255)         # #101A44
C_COBALT = (47, 102, 243, 255)    # #2F66F3
C_SOLAR = (255, 200, 61, 255)     # #FFC83D
C_MINT = (143, 225, 207, 255)     # #8FE1CF
C_CORAL = (255, 125, 114, 255)    # #FF7D72
C_IVORY = (255, 249, 241, 255)    # #FFF9F1
C_PAPER = (246, 242, 236, 255)    # #F6F2EC
C_LINE = (229, 222, 213, 255)     # #E5DED5
C_MUTED = (100, 112, 138, 255)    # #64708A
C_SUCCESS = (24, 138, 100, 255)   # #188A64
C_WHITE = (255, 255, 255, 255)

# Fonts
FONT_DIR = "/usr/share/fonts/truetype"
FONT_SANS_BOLD = f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"
FONT_SANS_REG = f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"
FONT_MONO_BOLD = f"{FONT_DIR}/freefont/FreeMonoBold.ttf"
FONT_MONO_REG = f"{FONT_DIR}/freefont/FreeMono.ttf"

f_hero = ImageFont.truetype(FONT_SANS_BOLD, 52)
f_title = ImageFont.truetype(FONT_SANS_BOLD, 38)
f_subtitle = ImageFont.truetype(FONT_SANS_REG, 20)
f_body = ImageFont.truetype(FONT_SANS_REG, 17)
f_kicker = ImageFont.truetype(FONT_MONO_BOLD, 14)
f_kicker_sm = ImageFont.truetype(FONT_MONO_BOLD, 12)
f_card_val = ImageFont.truetype(FONT_MONO_BOLD, 22)
f_card_lbl = ImageFont.truetype(FONT_MONO_REG, 12)
f_card_sub = ImageFont.truetype(FONT_SANS_BOLD, 11)
f_hash = ImageFont.truetype(FONT_MONO_BOLD, 13)
f_brand_lg = ImageFont.truetype(FONT_SANS_BOLD, 64)
f_brand_tag = ImageFont.truetype(FONT_SANS_BOLD, 22)

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
        print(f"Warning: image {p} not found, generating placeholder")
        im = Image.new("RGBA", (1920, 1080), C_PAPER)
        screenshots[k] = im

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def draw_top_bar(draw, frame_idx):
    # Top Left Brand
    draw_rounded_rect(draw, (80, 50, 124, 94), 10, fill=C_COBALT)
    draw.text((91, 58), "Th", font=ImageFont.truetype(FONT_SANS_BOLD, 24), fill=C_WHITE)
    draw.text((138, 56), "ThPay", font=ImageFont.truetype(FONT_SANS_BOLD, 24), fill=C_INK)
    
    # Pill
    draw_rounded_rect(draw, (230, 60, 420, 88), 6, fill=(16, 26, 68, 15))
    draw.text((242, 65), "CONTINUOUS PAYROLL", font=f_kicker_sm, fill=C_COBALT)

    # Top Right Timecode / Tag
    tc_sec = frame_idx // 30
    tc_frame = frame_idx % 30
    tc_str = f"REC  00:{tc_sec:02d}.{tc_frame:02d} / 00:20.00"
    draw.ellipse((1630, 69, 1640, 79), fill=(239, 68, 68, 255))
    draw.text((1650, 65), tc_str, font=f_kicker_sm, fill=C_MUTED)

def create_window_mockup(im_content, w, h, url="thpay.corp/dashboard"):
    mock = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(mock)

    # Shadow / Base
    draw_rounded_rect(mdraw, (0, 0, w, h), 16, fill=C_WHITE, outline=C_LINE, width=1)

    # Titlebar
    title_h = 36
    draw_rounded_rect(mdraw, (0, 0, w, title_h + 16), 16, fill=(248, 250, 252, 255))
    mdraw.rectangle((0, title_h, w, title_h + 16), fill=(248, 250, 252, 255))
    mdraw.line([(0, title_h + 16), (w, title_h + 16)], fill=C_LINE, width=1)

    # Dots
    mdraw.ellipse((16, 20, 26, 30), fill=(239, 68, 68, 255))
    mdraw.ellipse((34, 20, 44, 30), fill=(245, 158, 11, 255))
    mdraw.ellipse((52, 20, 62, 30), fill=(16, 185, 129, 255))

    # URL pill
    draw_rounded_rect(mdraw, (80, 16, min(w - 20, 360), 36), 6, fill=C_WHITE, outline=C_LINE, width=1)
    mdraw.text((95, 20), url, font=f_kicker_sm, fill=C_MUTED)

    # Body Content
    body_h = h - (title_h + 16)
    content_scaled = im_content.resize((w, body_h), Image.Resampling.LANCZOS)
    mock.paste(content_scaled, (0, title_h + 16))
    return mock

def render_scene_1(progress):
    # Hook Scene (0.0s - 3.5s)
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    # Subtle grid lines
    for x in range(0, WIDTH, 60):
        draw.line([(x, 0), (x, HEIGHT)], fill=(16, 26, 68, 8), width=1)
    for y in range(0, HEIGHT, 60):
        draw.line([(0, y), (WIDTH, y)], fill=(16, 26, 68, 8), width=1)

    # Center animation
    fade = min(1.0, progress * 3.0)
    y_offset = int((1.0 - fade) * 40)

    # Kicker
    kicker_box = (820, 260 - y_offset, 1100, 298 - y_offset)
    draw_rounded_rect(draw, kicker_box, 19, fill=(47, 102, 243, 25))
    draw.text((845, 271 - y_offset), "MUDANÇA DE PARADIGMA", font=f_kicker, fill=C_COBALT)

    # Big Heading
    h1 = "O fechamento mensal de folha acabou."
    h2 = "Conheça o Continuous Payroll em tempo real."
    draw.text((960, 360 - y_offset), h1, font=f_hero, fill=C_INK, anchor="mm")
    draw.text((960, 435 - y_offset), h2, font=f_hero, fill=C_COBALT, anchor="mm")

    # Lead
    lead = "Cada lançamento, benefício ou ajuste recalcula a remuneração instantaneamente. Sem surpresas no dia 5."
    draw.text((960, 520 - y_offset), lead, font=f_subtitle, fill=C_MUTED, anchor="mm")

    # 4 Feature Pills
    pills = [
        ("400 Colaboradores Ativos", C_MINT),
        ("Latência Wasm < 1ms", C_SOLAR),
        ("eSocial v1.3 Desacoplado", C_COBALT),
        ("Guia FGTS Digital via Pix", C_SUCCESS)
    ]
    card_w = 260
    card_gap = 24
    total_w = len(pills) * card_w + (len(pills) - 1) * card_gap
    start_x = (WIDTH - total_w) // 2
    card_y = 620 - y_offset

    for idx, (label, dot_col) in enumerate(pills):
        cx = start_x + idx * (card_w + card_gap)
        draw_rounded_rect(draw, (cx, card_y, cx + card_w, card_y + 54), 12, fill=C_WHITE, outline=C_LINE, width=1)
        draw.ellipse((cx + 18, card_y + 22, cx + 30, card_y + 34), fill=dot_col)
        draw.text((cx + 40, card_y + 19), label, font=ImageFont.truetype(FONT_SANS_BOLD, 14), fill=C_INK)

    return im

def render_scene_2(progress):
    # Executive Dashboard (3.5s - 7.5s)
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    # Left Side: Info & Metric Cards
    draw_rounded_rect(draw, (100, 160, 380, 192), 16, fill=(47, 102, 243, 20))
    draw.text((116, 168), "DASHBOARD EXECUTIVO CONSOLIDADO", font=f_kicker_sm, fill=C_COBALT)

    draw.text((100, 215), "Visão Geral da Folha Sem Exposição Nominal", font=f_title, fill=C_INK)
    draw.text((100, 275), "Métricas macroeconômicas, barra de prontidão e gráficos em tempo real.", font=f_subtitle, fill=C_MUTED)

    # 4 Cards Grid (2x2)
    cards = [
        ("CUSTO TOTAL DE PESSOAL", "R$ 8.340.456,01", "Fator real 1.68x sobre base", C_INK),
        ("LÍQUIDO A PAGAR (REMESSA)", "R$ 4.841.990,13", "300 CLT • 100 PJ", C_COBALT),
        ("BARRA DE PRONTIDÃO (READINESS)", "98,2%", "1 divergência de ponto", C_SUCCESS),
        ("TRIBUTOS & ENCARGOS PATRONAIS", "R$ 1.463.562,15", "DARF + FGTS Digital Pix", C_CORAL)
    ]

    for idx, (lbl, val, sub, col) in enumerate(cards):
        gx = 100 + (idx % 2) * 360
        gy = 340 + (idx // 2) * 135
        draw_rounded_rect(draw, (gx, gy, gx + 340, gy + 115), 14, fill=C_WHITE, outline=C_LINE, width=1)
        draw.text((gx + 18, gy + 16), lbl, font=f_card_lbl, fill=C_MUTED)
        draw.text((gx + 18, gy + 42), val, font=f_card_val, fill=col)
        draw.text((gx + 18, gy + 82), sub, font=f_card_sub, fill=C_MUTED)

    # Bottom Highlight Pill
    draw_rounded_rect(draw, (100, 640, 800, 700), 12, fill=C_WHITE, outline=C_LINE, width=1)
    draw.text((120, 655), "Quadro Geral Ativo: 400 Vidas Processadas com Hash SHA-256", font=ImageFont.truetype(FONT_SANS_BOLD, 15), fill=C_INK)

    # Right Side: Window Mockup with subtle Ken Burns zoom
    mw, mh = 960, 640
    zoom = 1.0 + 0.05 * progress
    scr = screenshots["01_dashboard_folha_continua.png"]
    crop_w = int(scr.width / zoom)
    crop_h = int(scr.height / zoom)
    scr_crop = scr.crop((0, 0, crop_w, crop_h))
    mock = create_window_mockup(scr_crop, mw, mh, "thpay.corp/dashboard/executive")
    im.paste(mock, (880, 160), mock)

    return im

def render_scene_3(progress):
    # Live Payslip Inspector Drawer (7.5s - 11.5s)
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    # Left Side: Explanation
    draw_rounded_rect(draw, (100, 160, 370, 192), 16, fill=(47, 102, 243, 20))
    draw.text((116, 168), "RAIO-X CENTAVO A CENTAVO", font=f_kicker_sm, fill=C_COBALT)

    draw.text((100, 215), "Gaveta Lateral de Holerite em Tempo Real", font=f_title, fill=C_INK)
    draw.text((100, 275), "Inspecione a anatomia exata de cada remuneração sem perder o contexto.", font=f_subtitle, fill=C_MUTED)

    # Highlights
    features = [
        ("Precisão Financeira Estrita", "Java 21 LTS BigDecimal elimina erros de ponto flutuante."),
        ("Tributação Progressiva", "INSS conforme EC 103/2019 e cálculo do IRRF Legal e Simplificado."),
        ("Benefícios & Provisões", "Split flexível de VA/VR, opt-out de VT e reflexos patronais.")
    ]
    for idx, (h_title, h_desc) in enumerate(features):
        fy = 350 + idx * 105
        draw_rounded_rect(draw, (100, fy, 800, fy + 85), 12, fill=C_WHITE, outline=C_LINE, width=1)
        draw_rounded_rect(draw, (100, fy, 108, fy + 85), 12, fill=C_COBALT)
        draw.text((125, fy + 18), h_title, font=ImageFont.truetype(FONT_SANS_BOLD, 17), fill=C_INK)
        draw.text((125, fy + 48), h_desc, font=f_body, fill=C_MUTED)

    # Right Side: Window Mockup of Drawer
    mw, mh = 960, 640
    slide_in = min(1.0, progress * 2.5)
    off_x = int((1.0 - slide_in) * 150)
    mock = create_window_mockup(screenshots["02_raio_x_holerite_drawer.png"], mw, mh, "thpay.corp/directory/inspector")
    im.paste(mock, (880 + off_x, 160), mock)

    return im

def render_scene_4(progress):
    # Batch Admissions & FGTS Digital Pix (11.5s - 15.5s)
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    # Left Side
    draw_rounded_rect(draw, (100, 160, 390, 192), 16, fill=(47, 102, 243, 20))
    draw.text((116, 168), "CONFORMIDADE & AUTOMAÇÃO", font=f_kicker_sm, fill=C_COBALT)

    draw.text((100, 215), "Admissões em Massa & eSocial via Pix", font=f_title, fill=C_INK)
    draw.text((100, 275), "Onboarding de lotes com parser inteligente e quitação instantânea de guias.", font=f_subtitle, fill=C_MUTED)

    cards = [
        ("LOTE DE ADMISSÃO EM MASSA", "50 Colaboradores", "Eventos S-2190 e S-2200 gerados", C_INK),
        ("FGTS DIGITAL & DARF", "QR Code Pix Nativo", "Baixa e compensação imediata", C_SUCCESS)
    ]
    for idx, (lbl, val, sub, col) in enumerate(cards):
        cy = 350 + idx * 130
        draw_rounded_rect(draw, (100, cy, 800, cy + 110), 14, fill=C_WHITE, outline=C_LINE, width=1)
        draw.text((124, cy + 18), lbl, font=f_card_lbl, fill=C_MUTED)
        draw.text((124, cy + 44), val, font=f_card_val, fill=col)
        draw.text((124, cy + 80), sub, font=f_card_sub, fill=C_MUTED)

    # Right Side: Split view of Admissions and Pix
    mw, mh = 960, 640
    active_img = screenshots["08_esocial_guias_pix.png"] if progress > 0.5 else screenshots["09_admissoes_lotes_onboarding.png"]
    url = "thpay.corp/esocial/pix-digital" if progress > 0.5 else "thpay.corp/admissions/batches"
    mock = create_window_mockup(active_img, mw, mh, url)
    im.paste(mock, (880, 160), mock)

    return im

def render_scene_5(progress):
    # Official Payslip & Brand Finale (15.5s - 20.0s)
    im = Image.new("RGBA", (WIDTH, HEIGHT), C_IVORY)
    draw = ImageDraw.Draw(im)

    if progress < 0.55:
        # Phase A: Payslip with Cryptographic Stamp
        draw_rounded_rect(draw, (100, 160, 390, 192), 16, fill=(47, 102, 243, 20))
        draw.text((116, 168), "INTEGRIDADE CRIPTOGRÁFICA", font=f_kicker_sm, fill=C_COBALT)

        draw.text((100, 215), "Holerite Oficial e Canhoto ABNT", font=f_title, fill=C_INK)
        draw.text((100, 275), "Assinatura digital e hash SHA-256 em cada folha gerada.", font=f_subtitle, fill=C_MUTED)

        # Hash Box
        draw_rounded_rect(draw, (100, 350, 800, 470), 14, fill=C_WHITE, outline=C_LINE, width=1)
        draw.text((125, 370), "HASH SHA-256 DO HOLERITE (AUDITORIA IMUTÁVEL)", font=f_kicker_sm, fill=C_MUTED)
        draw.text((125, 400), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", font=f_hash, fill=C_COBALT)
        draw.text((125, 435), "Emissão oficial com recibo de quitação e bases eSocial/FGTS consolidadas.", font=f_body, fill=C_SUCCESS)

        # Right Side Mockup
        mw, mh = 960, 640
        mock = create_window_mockup(screenshots["10_impressao_holerite_oficial.png"], mw, mh, "thpay.corp/payslip/print-preview")
        im.paste(mock, (880, 160), mock)
    else:
        # Phase B: Grand Finale Brand Card
        fade = min(1.0, (progress - 0.55) * 4.0)
        draw_rounded_rect(draw, (100, 160, WIDTH - 100, HEIGHT - 120), 24, fill=C_WHITE, outline=C_LINE, width=2)

        # Big Badge
        draw_rounded_rect(draw, (910, 240, 1010, 340), 24, fill=C_COBALT)
        draw.text((932, 258), "Th", font=ImageFont.truetype(FONT_SANS_BOLD, 60), fill=C_WHITE)

        draw.text((960, 400), "ThPay", font=f_brand_lg, fill=C_INK, anchor="mm")
        draw.text((960, 460), "Tecnologia que cuida do processo e das pessoas.", font=f_brand_tag, fill=C_COBALT, anchor="mm")
        draw.text((960, 520), "Continuous Payroll • eSocial v1.3 Desacoplado • Determinismo Centavo a Centavo", font=f_subtitle, fill=C_MUTED, anchor="mm")

        # Tech Stack Badges
        techs = ["Java 21 LTS (Loom)", "Rust / WebAssembly", "Next.js 15", "Tailwind CSS", "Python / Polars", "Pix FGTS Digital"]
        tw = 180
        tgap = 18
        tot_tw = len(techs) * tw + (len(techs) - 1) * tgap
        st_x = (WIDTH - tot_tw) // 2
        for t_idx, tech in enumerate(techs):
            tx = st_x + t_idx * (tw + tgap)
            draw_rounded_rect(draw, (tx, 580, tx + tw, 624), 8, fill=C_PAPER, outline=C_LINE, width=1)
            draw.text((tx + tw // 2, 602), tech, font=f_kicker_sm, fill=C_INK, anchor="mm")

        draw_rounded_rect(draw, (840, 680, 1080, 734), 27, fill=C_SOLAR)
        draw.text((960, 707), "github.com/Taiwansz/ThPay", font=ImageFont.truetype(FONT_SANS_BOLD, 16), fill=C_INK, anchor="mm")

    return im

def generate_frame(frame_idx):
    t = frame_idx / FPS

    if t < 3.5:
        # Scene 1: 0.0 - 3.5s
        p = t / 3.5
        im = render_scene_1(p)
    elif t < 7.5:
        # Scene 2: 3.5 - 7.5s
        p = (t - 3.5) / 4.0
        im = render_scene_2(p)
    elif t < 11.5:
        # Scene 3: 7.5 - 11.5s
        p = (t - 7.5) / 4.0
        im = render_scene_3(p)
    elif t < 15.5:
        # Scene 4: 11.5 - 15.5s
        p = (t - 11.5) / 4.0
        im = render_scene_4(p)
    else:
        # Scene 5: 15.5 - 20.0s
        p = (t - 15.5) / 4.5
        im = render_scene_5(p)

    draw = ImageDraw.Draw(im)
    draw_top_bar(draw, frame_idx)

    # Master Fade Out on last 0.5s
    if t > 19.5:
        alpha = int(((20.0 - t) / 0.5) * 255)
        black_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (16, 26, 68, 255 - alpha))
        im = Image.alpha_composite(im, black_overlay)

    return im

def main():
    output_mp4 = "brag-output/brag.mp4"
    audio_wav = "brag-output/soundtrack.wav"

    print(f"Starting broadcast rendering pipeline: {WIDTH}x{HEIGHT} @ {FPS}fps ({TOTAL_FRAMES} frames)")

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
        "-crf", "18",  # High quality
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
        # Extract Poster Frame (Settled beat at 5.5s)
        poster_cmd = [
            "ffmpeg", "-y",
            "-ss", "5.5",
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
