# -*- coding: utf-8 -*-
"""Transforme l'export Claude Design en site statique de cinq pages."""
import json, re, base64, zlib, os, shutil, html

SRC = "source/export-claude-design.html"
OUT = "../site"

raw = open(SRC, encoding="utf-8").read()
manifest = json.loads(re.search(r'<script type="__bundler/manifest">(.*?)</script>', raw, re.S).group(1))
template = json.loads(re.search(r'<script type="__bundler/template">(.*?)</script>', raw, re.S).group(1))

def decode(v):
    d = base64.b64decode(v["data"])
    if v.get("compressed"):
        for wbits in (15, -15, 47):
            try: return zlib.decompress(d, wbits)
            except Exception: pass
        raise ValueError("décompression impossible")
    return d

# ---------------------------------------------------------------- 1. découpe
helmet = re.search(r'<helmet>(.*?)</helmet>', template, re.S).group(1)
corps = template[template.find("</helmet>") + len("</helmet>"):]
corps = corps[:corps.rfind("</x-dc>")] if "</x-dc>" in corps else corps

# CSS du système de design (le <style> du helmet)
css_sys = "\n".join(m.group(1) for m in re.finditer(r'<style>(.*?)</style>', helmet, re.S))

# ---------------------------------------------------------------- 2. polices
os.makedirs(OUT + "/assets/fonts", exist_ok=True)
# On ne garde que les sous-ensembles utiles au français : latin et latin-ext.
GARDE = ("U+0000-00FF", "U+0100-02BA")
gardees, jetees = {}, []
def nom_police(bloc):
    """Ces polices sont variables : un même fichier couvre 400 et 600. Le nom ne porte donc
    pas la graisse, et le fichier n'est écrit qu'une fois."""
    f = re.search(r"font-family:\s*'([^']+)'", bloc).group(1).replace(" ", "-").lower()
    r = re.search(r'unicode-range:\s*(U\+[0-9A-Fa-f-]+)', bloc)
    sub = "latin-ext" if (r and r.group(1).startswith("U+0100")) else "latin"
    return "%s-%s" % (f, sub)

blocs = []
for m in re.finditer(r'@font-face\s*\{(.*?)\}', css_sys, re.S):
    bloc = m.group(1)
    u = re.search(r'url\("([^"]+)"\)', bloc)
    r = re.search(r'unicode-range:\s*([^;]+);', bloc)
    if not u:
        continue
    uuid = u.group(1)
    plage = (r.group(1).strip() if r else "")
    if not any(plage.startswith(g) for g in GARDE):
        jetees.append(m.group(0)); continue
    nom = nom_police(bloc)
    if nom not in gardees:
        data = decode(manifest[uuid])
        open("%s/assets/fonts/%s.woff2" % (OUT, nom), "wb").write(data)
        gardees[nom] = len(data)
    blocs.append(bloc.replace('url("%s")' % uuid, 'url("/assets/fonts/%s.woff2")' % nom))

css_polices = "\n".join("@font-face {%s}" % b for b in blocs)
# le CSS système sans ses @font-face (remplacés ci-dessus)
css_sys = re.sub(r'@font-face\s*\{.*?\}\s*', '', css_sys, flags=re.S)
# commentaires de sous-ensembles devenus orphelins
css_sys = re.sub(r'/\*\s*(cyrillic|greek|vietnamese|latin)[^*]*\*/\s*', '', css_sys)

# ---------------------------------------------------------------- 3. sc-if
def eval_scif(src, vals):
    """Remplace <sc-if value="{{ cond }}">…</sc-if> en tenant compte de l'imbrication."""
    while True:
        m = re.search(r'<sc-if value="\{\{ (\w+) \}\}"[^>]*>', src)
        if not m:
            return src
        cond, i, j = m.group(1), m.start(), m.end()
        prof, k = 1, j
        while prof:
            n = re.search(r'<sc-if\b[^>]*>|</sc-if>', src[k:])
            if not n:
                raise ValueError("sc-if non fermé")
            prof += 1 if n.group(0).startswith("<sc-if") else -1
            k += n.end()
        interieur = src[j:k - len("</sc-if>")]
        src = src[:i] + (interieur if vals.get(cond) else "") + src[k:]

PAGES = [
    ("accueil",          "isAccueil", "",                  "index.html"),
    ("tarifs",           "isTarifs",  "tarifs",            "tarifs/index.html"),
    ("a-propos",         "isApropos", "a-propos",          "a-propos/index.html"),
    ("un-exemple",       "isExemple", "un-exemple",        "un-exemple/index.html"),
    ("mentions-legales", "isMentions","mentions-legales",  "mentions-legales/index.html"),
]

VIDES = {"br","img","input","meta","link","hr","path","rect","circle","line","polyline",
         "use","stop","source","area","col","embed","track","wbr","ellipse","polygon"}

def ajouter_classe(fragment, classe):
    """Ajoute une classe à chaque élément de premier niveau du fragment."""
    out, d, pos = [], 0, 0
    for tag in re.finditer(r'<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>', fragment):
        ouvrant, nom, attrs, auto = tag.groups()
        if d == 0 and not ouvrant:
            out.append(fragment[pos:tag.start()])
            # Le style en ligne l'emporte sur une feuille de style : on relève le mode
            # d'affichage pour pouvoir le rétablir exactement, sans deviner.
            md = re.search(r'display:\s*([a-z-]+)', attrs)
            classes = classe + (" aff-" + md.group(1) if md else "")
            if re.search(r'\bclass="([^"]*)"', attrs):
                attrs2 = re.sub(r'\bclass="([^"]*)"', lambda m: 'class="%s %s"' % (m.group(1), classes), attrs)
            else:
                attrs2 = attrs + ' class="%s"' % classes
            out.append("<%s%s%s>" % (nom, attrs2, auto))
            pos = tag.end()
        if ouvrant:
            d -= 1
        elif not auto and nom.lower() not in VIDES:
            d += 1
    out.append(fragment[pos:])
    return "".join(out)

def eval_scif2(src, vals):
    """Comme eval_scif, mais les blocs isWide/isNarrow sont conservés tous les deux
    et marqués d'une classe : le basculement à 900 px se fait en CSS, pas en JavaScript."""
    while True:
        m = re.search(r'<sc-if value="\{\{ (\w+) \}\}"[^>]*>', src)
        if not m:
            return src
        cond, i, j = m.group(1), m.start(), m.end()
        prof, k = 1, j
        while prof:
            n = re.search(r'<sc-if\b[^>]*>|</sc-if>', src[k:])
            if not n: raise ValueError("sc-if non fermé")
            prof += 1 if n.group(0).startswith("<sc-if") else -1
            k += n.end()
        interieur = src[j:k - len("</sc-if>")]
        if cond == "isWide":
            rendu = ajouter_classe(interieur, "sur-grand-ecran")
        elif cond == "isNarrow":
            rendu = ajouter_classe(interieur, "sur-petit-ecran")
        else:
            rendu = interieur if vals.get(cond) else ""
        src = src[:i] + rendu + src[k:]

LIENS = {"#accueil": "/", "#tarifs": "/tarifs/", "#a-propos": "/a-propos/",
         "#mentions-legales": "/mentions-legales/", "#un-exemple": "/un-exemple/"}

CSS_SITE = """
/* Basculement de mise en page à 900 px, en CSS : l'original le faisait en JavaScript.
   Les éléments concernés portent un style « display » en ligne, qui l'emporterait sur
   une simple règle de feuille de style. On le neutralise, puis on le rétablit à
   l'identique grâce à la classe aff-* posée à la conversion. */
.sur-grand-ecran, .sur-petit-ecran { display: none !important; }
@media (min-width: 900px) {
  .sur-grand-ecran { display: block !important; }
  .sur-grand-ecran.aff-flex { display: flex !important; }
  .sur-grand-ecran.aff-inline-flex { display: inline-flex !important; }
  .sur-grand-ecran.aff-grid { display: grid !important; }
  .sur-grand-ecran.aff-inline-block { display: inline-block !important; }
}
@media (max-width: 899.98px) {
  .sur-petit-ecran { display: block !important; }
  .sur-petit-ecran.aff-flex { display: flex !important; }
  .sur-petit-ecran.aff-inline-flex { display: inline-flex !important; }
  .sur-petit-ecran.aff-grid { display: grid !important; }
  .sur-petit-ecran.aff-inline-block { display: inline-block !important; }
}
/* Animations d'apparition : neutralisées si la personne a demandé moins d'animations. */
@media (prefers-reduced-motion: reduce) {
  [data-reveal], [data-frise-item], [data-frise-line] {
    opacity: 1 !important; transform: none !important; transition: none !important;
  }
}
img { max-width: 100%; height: auto; display: block; }
a:focus-visible, button:focus-visible {
  outline: 2px solid var(--color-accent-700); outline-offset: 2px; border-radius: 2px;
}
"""

JS_SITE = """/* Apparition au défilement. Respecte « réduire les animations ». */
(function () {
  var doux = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (doux || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target; io.unobserve(el);
      if (el.hasAttribute('data-frise')) {
        var ligne = el.querySelector('[data-frise-line]');
        if (ligne) ligne.style.transform = 'none';
        el.querySelectorAll('[data-frise-item]').forEach(function (it) {
          it.style.opacity = '1'; it.style.transform = 'none';
        });
      } else { el.style.opacity = '1'; el.style.transform = 'none'; }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  document.querySelectorAll('[data-reveal]').forEach(function (el) {
    el.style.opacity = '0'; el.style.transform = 'translateY(12px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    io.observe(el);
  });
  document.querySelectorAll('[data-frise]').forEach(function (el) {
    var x = el.getAttribute('data-axis') === 'x';
    var items = el.querySelectorAll('[data-frise-item]');
    var ligne = el.querySelector('[data-frise-line]');
    var pas = 0.22;
    if (ligne) {
      ligne.style.transform = x ? 'scaleX(0)' : 'scaleY(0)';
      ligne.style.transition = 'transform ' + (items.length * pas + 0.2) + 's ease-out';
    }
    items.forEach(function (it, i) {
      it.style.opacity = '0';
      it.style.transform = x ? 'translateY(6px)' : 'translateX(-6px)';
      it.style.transition = 'opacity .4s ease ' + (i * pas) + 's, transform .4s ease ' + (i * pas) + 's';
    });
    io.observe(el);
  });
})();
"""

SITE = "https://marches-publics.studiomathysbocage.fr"
DESC_ACCUEIL = ("Analyse des consultations, rédaction des mémoires techniques, constitution des dossiers "
                "de candidature et d’offre. Artisans et petites entreprises de Guadeloupe.")
META = {
  "accueil": ("Mathys Bocage · Assistance à la réponse aux marchés publics", DESC_ACCUEIL),
  "tarifs": ("Tarifs et conditions · Mathys Bocage",
             "Forfait de 690 € pour un dossier normal, 890 € pour un dossier important. Prime de succès de 1,5 % "
             "du montant du marché signé, plafonnée à 1 500 €. Conditions de délai et de paiement."),
  "a-propos": ("À propos · Mathys Bocage",
               "Mathys Bocage, entreprise individuelle à Baie-Mahault. Licence de droit, premier prix du concours "
               "Entreprendre de l’Université des Antilles 2025. Périmètre de la mission et confidentialité."),
  "un-exemple": ("Un exemple · Mathys Bocage",
                 "Une fiche d’analyse réelle, publiée après la date limite de dépôt."),
  "mentions-legales": ("Mentions légales · Mathys Bocage",
                       "Éditeur, hébergeur et traitement des données du site d’assistance à la réponse aux marchés publics."),
}
IMAGES = {
  # Les proportions reprennent celles des conteneurs du gabarit d'origine.
  "photo-hero-chantier": dict(fichier="chantier", ratio=(1000, 1250), largeurs=(500, 1000), eager=True,
                              alt="Bâtiment en construction, ossature de béton et planchers encore à nu"),
  "photo-mathys-rond":   dict(fichier="mathys-bocage-portrait", ratio=(224, 224), largeurs=(112, 224), eager=True,
                              cercle=True, alt="Mathys Bocage, portrait"),
  "photo-bande-plan":    dict(fichier="plan-chantier", ratio=(1680, 640), largeurs=(840, 1680), eager=False,
                              alt="Une main tient un crayon au-dessus d’un plan technique déplié"),
  "photo-bande-facade":  dict(fichier="facade-echafaudage", ratio=(1680, 560), largeurs=(840, 1680), eager=True,
                              alt="Échafaudage dressé devant la façade en brique d’un immeuble en rénovation"),
  "photo-trophee":       dict(fichier="mathys-bocage-trophee", ratio=(1000, 1250), largeurs=(500, 1000), eager=False,
                              alt="Mathys Bocage tenant le trophée du concours Entreprendre"),
}

def balise_image(pid):
    o = IMAGES[pid]; f = o["fichier"]; w, h = o["ratio"]; p1, p2 = o["largeurs"]
    rayon = "border-radius:50%;" if o.get("cercle") else ""
    if o.get("cercle"):
        srcset = 'srcset="/assets/img/%s-%d.jpg 1x, /assets/img/%s-%d.jpg 2x" ' % (f, p1, f, p2)
        sizes = ""
    else:
        srcset = 'srcset="/assets/img/%s-%d.jpg %dw, /assets/img/%s-%d.jpg %dw" ' % (f, p1, p1, f, p2, p2)
        sizes = 'sizes="(max-width: 900px) 100vw, %dpx" ' % p2
    return ('<img src="/assets/img/%s-%d.jpg" %s%salt="%s" width="%d" height="%d" '
            'loading="%s" decoding="async" '
            'style="width:100%%;height:100%%;object-fit:cover;%s">'
            % (f, p1, srcset, sizes, html.escape(o["alt"], quote=True), w, h,
               "eager" if o["eager"] else "lazy", rayon))

def tete(cle, chemin):
    titre, desc = META[cle]
    url = SITE + "/" + (chemin + "/" if chemin else "")
    robots = '\n  <meta name="robots" content="noindex, nofollow">' if cle == "un-exemple" else ""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%s</title>
  <meta name="description" content="%s">%s
  <link rel="canonical" href="%s">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Mathys Bocage · Marchés publics">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:url" content="%s">
  <meta property="og:title" content="%s">
  <meta property="og:description" content="%s">
  <meta property="og:image" content="%s/assets/img/apercu-lien.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Mathys Bocage, assistance à la réponse aux marchés publics en Guadeloupe">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="%s">
  <meta name="twitter:description" content="%s">
  <meta name="twitter:image" content="%s/assets/img/apercu-lien.jpg">
  <meta name="theme-color" content="#f3f2f2">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="stylesheet" href="/assets/site.css">
</head>
<body>
""" % (html.escape(titre), html.escape(desc, quote=True), robots, url, url,
       html.escape(META["accueil"][0] if cle == "accueil" else titre, quote=True),
       html.escape(desc, quote=True), SITE,
       html.escape(META["accueil"][0] if cle == "accueil" else titre, quote=True),
       html.escape(desc, quote=True), SITE)

# ---------------------------------------------------------------- 4. assemblage
def nettoyer(frag):
    # liens d'ancre -> adresses réelles
    for a, b in LIENS.items():
        frag = frag.replace('href="%s"' % a, 'href="%s"' % b)
    # emplacements photo -> vraies images
    def rempl(m):
        pid = re.search(r'id="([^"]+)"', m.group(0)).group(1)
        return balise_image(pid) if pid in IMAGES else ""
    frag = re.sub(r'<image-slot\b[^>]*></image-slot>', rempl, frag)
    # Les légendes visibles reprenaient les descriptions des emplacements photo, qui
    # n'étaient que des indications de choix. Elles disparaissent ; le texte alternatif reste.
    frag = re.sub(r'<figcaption\b[^>]*>.*?</figcaption>\s*', '', frag, flags=re.S)
    # bandeau Claude Design
    frag = re.sub(r'<div id="__claude_design_branding".*?</div>\s*', '', frag, flags=re.S)
    frag = re.sub(r'<a[^>]+claude\.com/product/design[^>]*>.*?</a>\s*', '', frag, flags=re.S)
    # scripts du moteur Claude Design
    frag = re.sub(r'<script\b[^>]*>.*?</script>\s*', '', frag, flags=re.S)
    # corrections demandées dans le brief
    frag = frag.replace("Cette page n’utilise ni traceur ni cookie",
                        "Ce site n’utilise ni traceur ni cookie")
    frag = frag.replace("[nom, adresse et téléphone de l’hébergeur]", HEBERGEUR)
    return frag

HEBERGEUR = ("Netlify, Inc., 101 2nd Street, San Francisco, CA 94105, États-Unis. "
             "Netlify ne publie pas de numéro de téléphone ; le contact se fait à l’adresse "
             "<a href=\"mailto:privacy@netlify.com\" style=\"color:var(--color-accent-700)\">privacy@netlify.com</a> "
             "ou depuis <a href=\"https://www.netlify.com/contact/\" style=\"color:var(--color-accent-700)\">netlify.com/contact</a>")

os.makedirs(OUT + "/assets/img", exist_ok=True)
open(OUT + "/assets/site.css", "w", encoding="utf-8").write(css_polices + "\n" + css_sys + "\n" + CSS_SITE)
open(OUT + "/assets/site.js", "w", encoding="utf-8").write(JS_SITE)

# Chaque section est déjà enveloppée dans son propre <sc-if> : il suffit d'évaluer
# les conditions sur le corps entier, comme le faisait le moteur d'origine.

rapport = []
for cle, cond, chemin, fichier in PAGES:
    vals = {c: False for c in ("isAccueil", "isTarifs", "isApropos", "isExemple", "isMentions")}
    vals[cond] = True
    vals["showLaunchOffer"] = True
    page = eval_scif2(corps, vals)
    for p, var in (("accueil", "decoAccueil"), ("tarifs", "decoTarifs"), ("a-propos", "decoApropos")):
        page = page.replace("{{ %s }}" % var, "underline" if cle == p else "none")
    page = nettoyer(page)
    # lien « page en cours » pour les lecteurs d'écran
    cible = LIENS.get("#" + cle, "/")
    page = page.replace('href="%s"' % cible, 'href="%s" aria-current="page"' % cible, 1)
    doc = tete(cle, chemin) + page + '\n<script src="/assets/site.js" defer></script>\n</body>\n</html>\n'
    dest = os.path.join(OUT, fichier)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(doc)
    rapport.append((fichier, len(doc.encode("utf-8"))))

print("Polices conservées (%d) :" % len(gardees))
for n, t_ in sorted(gardees.items()):
    print("   %-34s %6.1f Ko" % (n, t_ / 1024))
print("Sous-ensembles écartés (cyrillique, grec, vietnamien…) : %d" % len(jetees))
print("\nCSS : %6.1f Ko   JS : %4.1f Ko" % (
    os.path.getsize(OUT + "/assets/site.css") / 1024, os.path.getsize(OUT + "/assets/site.js") / 1024))
print("\nPages écrites :")
for f, n in rapport:
    print("   %-32s %6.1f Ko de HTML" % (f, n / 1024))
