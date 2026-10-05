# -*- coding: utf-8 -*-
"""Recadre, redimensionne et compresse les images du site."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
OUT = "../site/assets/img"
os.makedirs(OUT, exist_ok=True)

def preparer(src, base, largeurs, ratio, ancrage=0.5, qualite=78):
    im = Image.open(src).convert("RGB")
    cible = ratio[0] / ratio[1]
    actuel = im.width / im.height
    if actuel > cible:                       # trop large : on rogne les côtés
        nw = int(im.height * cible)
        x = int((im.width - nw) * 0.5)
        im = im.crop((x, 0, x + nw, im.height))
    else:                                    # trop haut : on rogne en hauteur
        nh = int(im.width / cible)
        y = int((im.height - nh) * ancrage)
        im = im.crop((0, y, im.width, y + nh))
    sorties = []
    for L in largeurs:
        H = max(1, round(L * ratio[1] / ratio[0]))
        v = im.resize((L, H), Image.LANCZOS)
        chemin = "%s/%s-%d.jpg" % (OUT, base, L)
        # Les grandes variantes sont un peu plus compressées : elles ne servent qu'aux
        # grands écrans, où le défaut se voit moins et où le poids compte davantage.
        q = qualite - 6 if L >= 1000 else qualite
        v.save(chemin, "JPEG", quality=q, optimize=True, progressive=True)
        sorties.append((chemin, os.path.getsize(chemin)))
    return sorties

def cale(base, largeurs, ratio, legende):
    """Image provisoire, le temps que les photos d'ambiance soient choisies."""
    for L in largeurs:
        H = max(1, round(L * ratio[1] / ratio[0]))
        im = Image.new("RGB", (L, H), (233, 226, 212))
        d = ImageDraw.Draw(im)
        for i in range(0, L + H, 46):
            d.line([(i, 0), (i - H, H)], fill=(216, 205, 185), width=10)
        try:
            police = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", max(13, L // 34))
        except Exception:
            police = ImageFont.load_default()
        txt = "PHOTO À CHOISIR\n" + legende
        bb = d.multiline_textbbox((0, 0), txt, font=police, align="center", spacing=8)
        d.rectangle([ (L - (bb[2]-bb[0]))//2 - 18, (H - (bb[3]-bb[1]))//2 - 14,
                      (L + (bb[2]-bb[0]))//2 + 18, (H + (bb[3]-bb[1]))//2 + 14 ], fill=(248, 244, 236))
        d.multiline_text(((L - (bb[2]-bb[0]))//2, (H - (bb[3]-bb[1]))//2), txt,
                         font=police, fill=(125, 84, 17), align="center", spacing=8)
        im.save("%s/%s-%d.jpg" % (OUT, base, L), "JPEG", quality=70, optimize=True)

total = []
# Photos de Mathys Bocage. Le portrait est cadré haut pour garder le visage dans le rond.
total += preparer("photos/mathys-bocage-portrait.jpg", "mathys-bocage-portrait", (112, 224), (1, 1), ancrage=0.12, qualite=84)
total += preparer("photos/mathys-bocage-trophee.jpg", "mathys-bocage-trophee", (500, 1000), (4, 5), ancrage=0.18)
# Photos d'ambiance retenues (Pexels). Ancrage choisi pour garder le sujet au centre du cadrage.
total += preparer("photos-ambiance/chantier.jpg", "chantier", (500, 1000), (4, 5), ancrage=0.42)
total += preparer("photos-ambiance/plan.jpg", "plan-chantier", (840, 1680), (21, 8), ancrage=0.56)
total += preparer("photos-ambiance/facade.jpg", "facade-echafaudage", (840, 1680), (21, 7), ancrage=0.40)
for f in sorted(os.listdir(OUT)):
    print("   %-40s %6.1f Ko" % (f, os.path.getsize(OUT + "/" + f) / 1024))
