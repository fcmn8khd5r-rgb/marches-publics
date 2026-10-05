# -*- coding: utf-8 -*-
"""Icône, image d'aperçu de lien, robots.txt, sitemap.xml, en-têtes Netlify."""
import os
from PIL import Image, ImageDraw, ImageFont
OUT = "../site"
SITE = "https://marches-publics.studiomathysbocage.fr"

# --- icône : le monogramme du système de design
FAVICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="MB">
  <rect width="100" height="100" rx="12" fill="#f5efe3"/>
  <text x="50" y="63" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif"
        font-size="40" font-weight="600" fill="#7d5411">MB</text>
  <rect x="28" y="72" width="44" height="2.5" fill="#b68235"/>
</svg>
'''
open(OUT + "/favicon.svg", "w", encoding="utf-8").write(FAVICON)

def police(taille):
    for p in ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
              "/System/Library/Fonts/Supplemental/Georgia.ttf",
              "/System/Library/Fonts/Supplemental/Times New Roman.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, taille)
            except Exception: pass
    return ImageFont.load_default()

# --- icône pour l'écran d'accueil iPhone
ico = Image.new("RGB", (180, 180), (245, 239, 227))
d = ImageDraw.Draw(ico)
f = police(74)
bb = d.textbbox((0, 0), "MB", font=f)
d.text(((180 - (bb[2]-bb[0]))/2 - bb[0], (180 - (bb[3]-bb[1]))/2 - bb[1] - 6), "MB", font=f, fill=(125, 84, 17))
d.rectangle([52, 126, 128, 131], fill=(182, 130, 53))
ico.save(OUT + "/apple-touch-icon.png", "PNG", optimize=True)

# --- image d'aperçu de lien : la photo d'accueil, recadrée, avec un bandeau de titre
src = OUT + "/assets/img/chantier-1000.jpg"
base = Image.open(src).convert("RGB")
cible = 1200 / 630
if base.width / base.height > cible:
    nw = int(base.height * cible); x = (base.width - nw) // 2
    base = base.crop((x, 0, x + nw, base.height))
else:
    nh = int(base.width / cible); y = int((base.height - nh) * 0.35)
    base = base.crop((0, y, base.width, y + nh))
og = base.resize((1200, 630), Image.LANCZOS)
d = ImageDraw.Draw(og, "RGBA")
d.rectangle([0, 630 - 212, 1200, 630], fill=(32, 31, 29, 232))
d.text((64, 630 - 176), "Mathys Bocage", font=police(50), fill=(250, 246, 238))
d.text((64, 630 - 112), "Assistance à la réponse aux marchés publics", font=police(36), fill=(225, 173, 102))
d.text((64, 630 - 58), "Artisans et petites entreprises de Guadeloupe", font=police(27), fill=(190, 184, 176))
d.rectangle([0, 630 - 216, 1200, 630 - 212], fill=(182, 130, 53, 255))
og.save(OUT + "/assets/img/apercu-lien.jpg", "JPEG", quality=84, optimize=True, progressive=True)

# --- robots.txt : la page « Un exemple » n'est pas indexée
open(OUT + "/robots.txt", "w", encoding="utf-8").write(
    "User-agent: *\nAllow: /\nDisallow: /un-exemple/\n\nSitemap: %s/sitemap.xml\n" % SITE)

# --- sitemap : les quatre pages publiques
pages = ["/", "/tarifs/", "/a-propos/", "/mentions-legales/"]
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p in pages:
    xml.append("  <url><loc>%s%s</loc></url>" % (SITE, p))
xml.append("</urlset>")
open(OUT + "/sitemap.xml", "w", encoding="utf-8").write("\n".join(xml) + "\n")

# --- en-têtes Netlify : cache long sur les ressources, et quelques protections
open(OUT + "/_headers", "w", encoding="utf-8").write("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; base-uri 'self'; form-action 'none'; frame-ancestors 'self'

/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/assets/img/*
  Cache-Control: public, max-age=31536000, immutable

/assets/site.css
  Cache-Control: public, max-age=604800

/assets/site.js
  Cache-Control: public, max-age=604800
""")

open(OUT + "/_redirects", "w", encoding="utf-8").write(
    "# Les anciennes adresses à ancre renvoient vers les vraies pages.\n"
    "/index.html    /    301!\n")

for f in ("favicon.svg", "apple-touch-icon.png", "assets/img/apercu-lien.jpg", "robots.txt", "sitemap.xml", "_headers", "_redirects"):
    print("   %-30s %6.1f Ko" % (f, os.path.getsize(OUT + "/" + f) / 1024))
