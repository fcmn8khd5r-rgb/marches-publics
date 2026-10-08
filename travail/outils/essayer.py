# -*- coding: utf-8 -*-
"""Sert le dossier public/ en appliquant VRAIMENT les en-têtes du fichier public/_headers.

    python3 travail/outils/essayer.py        puis http://127.0.0.1:8790

À utiliser avant chaque mise en ligne. Un serveur ordinaire ignore le fichier
_headers, qui n'est lu que par Netlify : c'est ainsi qu'une politique de sécurité
trop stricte a pu passer inaperçue en local et casser toute la mise en forme en
ligne. Ce petit serveur reproduit le comportement de Netlify."""
import http.server, socketserver, os, re, sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUBLIC = os.path.join(RACINE, "public")

def lire_entetes(chemin):
    """Lit public/_headers : { motif: [(nom, valeur), ...] }."""
    regles, motif = {}, None
    if not os.path.exists(chemin):
        return regles
    for ligne in open(chemin, encoding="utf-8"):
        nue = ligne.rstrip("\n")
        if not nue.strip() or nue.lstrip().startswith("#"):
            continue
        if not nue.startswith((" ", "\t")):
            motif = nue.strip(); regles[motif] = []
        elif motif and ":" in nue:
            nom, _, val = nue.strip().partition(":")
            regles[motif].append((nom.strip(), val.strip()))
    return regles

REGLES = lire_entetes(os.path.join(PUBLIC, "_headers"))

def correspond(motif, chemin):
    return re.fullmatch(re.escape(motif).replace(r"\*", ".*"), chemin) is not None

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        chemin = self.path.split("?")[0]
        for motif, entetes in REGLES.items():
            if correspond(motif, chemin):
                for nom, val in entetes:
                    self.send_header(nom, val)
        super().end_headers()
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
    os.chdir(PUBLIC)
    print("en-têtes appliqués :", ", ".join(REGLES) or "aucun")
    print("site d'essai : http://127.0.0.1:%d" % port)
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.TCPServer(("127.0.0.1", port), H).serve_forever()
