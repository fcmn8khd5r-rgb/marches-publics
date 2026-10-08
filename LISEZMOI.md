# Site « Mathys Bocage · Marchés publics »

Adresse prévue : https://marches-publics.studiomathysbocage.fr

Ce dépôt est **distinct** de celui de studiomathysbocage.fr. Les deux sites n'ont
aucun fichier en commun et ne se gênent pas.

## Les deux dossiers

| Dossier | Ce qu'il contient | En ligne ? |
|---|---|---|
| `public/` | Le site lui-même : les cinq pages, les images, les polices, la feuille de style. | **Oui.** C'est ce dossier que Netlify publie. |
| `travail/` | La consigne, l'export Claude Design d'origine, les crédits photo, la planche de contact, les photos en pleine résolution et les trois petits programmes de fabrication. | **Non.** Rien de ce dossier n'est accessible depuis le site. |

## Réglage Netlify

- **Dossier à publier** : `public`
- **Commande de construction** : aucune

Ces deux réglages sont déjà écrits dans `netlify.toml`, à la racine. Netlify le lit
tout seul : il n'y a rien à saisir dans son interface.

## Les cinq pages

| Adresse | Fichier |
|---|---|
| `/` | `public/index.html` |
| `/tarifs/` | `public/tarifs/index.html` |
| `/a-propos/` | `public/a-propos/index.html` |
| `/mentions-legales/` | `public/mentions-legales/index.html` |
| `/un-exemple/` | `public/un-exemple/index.html` |

La page « Un exemple » n'est reliée à aucun menu et porte une consigne de
non-indexation : les moteurs de recherche l'ignorent. Elle est aussi écartée dans
`public/robots.txt`.

## Essayer le site avant de le mettre en ligne

    python3 travail/outils/essayer.py

Puis ouvrir http://127.0.0.1:8790. Ce petit serveur applique les en-têtes du fichier
`public/_headers`, que Netlify lit mais qu'un serveur ordinaire ignore. C'est important :
une politique de sécurité trop stricte a déjà cassé toute la mise en forme en ligne
alors que tout paraissait normal en local. À utiliser avant chaque mise en ligne.

## Changer un texte

Les pages sont des fichiers HTML ordinaires. Pour corriger une phrase, ouvrez le
fichier de la page concernée, modifiez le texte entre les balises, enregistrez,
puis envoyez la modification sur GitHub. Netlify republie tout seul.

Attention : l'en-tête et le pied de page sont recopiés dans les cinq fichiers. Une
correction qui les concerne est donc à faire cinq fois.

## Refabriquer le site depuis l'export Claude Design

Utile seulement si la maquette change. Depuis `travail/outils/` :

    python3 convertir.py   # reconstruit les cinq pages et la feuille de style
    python3 images.py      # recadre et compresse les photos
    python3 annexes.py     # icône, image d'aperçu de lien, robots.txt, plan du site

Ces programmes attendent l'arborescence d'origine ; relisez-les avant de les lancer.

## Ce que le site ne fait pas

Aucun script venu d'ailleurs, aucune mesure d'audience, aucune police chargée
depuis un autre serveur, aucun traceur, aucun cookie. La phrase des mentions
légales sur les traceurs est donc exacte, et doit le rester.
