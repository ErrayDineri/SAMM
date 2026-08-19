# SAMM — Assistant intelligent de recherche de composants industriels

Application Streamlit qui traduit un besoin exprimé en langage naturel
(ex : *« créer un départ moteur triphasé »*) en une liste de composants,
puis retrouve les références correspondantes déjà disponibles dans le
stock de l'entreprise — via un LLM local (LM Studio) plutôt qu'une simple
recherche par mot-clé. Objectif : réduire les achats redondants et les
invendus de stock.

---

## ⚠️ À vérifier avant de lancer l'appli

`streamlitapp.py` charge actuellement :

```python
@st.cache_resource
def charger_stock():
    return Stock("named_stock.xlsx")
```

Or **`named_stock.xlsx` a des `ref` regroupées/filtrées** (transformées par
`filtre_stock.py`), pas les références d'origine. Le fichier destiné à
l'appli est **`stock_avec_nom_complet.xlsx`**, produit par
`fusionner_nom_complet.py`, qui contient les `ref` **intactes** + la
colonne `nom_complet`. Pense à changer cette ligne avant utilisation réelle :

```python
return Stock("stock_avec_nom_complet.xlsx")
```

(voir la section [Pipeline de préparation des données](#pipeline-de-préparation-des-données) pour comprendre pourquoi).

---

## Sommaire

- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration de LM Studio](#configuration-de-lm-studio)
- [Pipeline de préparation des données](#pipeline-de-préparation-des-données)
- [Lancer l'application](#lancer-lapplication)
- [Le système de kits](#le-système-de-kits)
- [Mode debug](#mode-debug)
- [Structure des fichiers](#structure-des-fichiers)
- [Dépannage](#dépannage)

---

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│  Technicien      │ ---> │  streamlitapp.py     │ ---> │  Résultats en   │
│  (besoin en      │      │  (interface web)     │      │  cartes + table │
│  langage naturel)│      └──────────┬───────────┘      └─────────────────┘
└─────────────────┘                  │
                                      ▼
                   ┌──────────────────────────────────┐
                   │  llm.py                          │
                   │  - choisit un kit existant, OU    │
                   │  - propose une liste de pièces    │
                   │  - fait correspondre chaque pièce │
                   │    à des "nom_complet" du stock   │
                   │  (appels à LM Studio, en local)   │
                   └──────────────┬────────────────────┘
                                  │
                   ┌──────────────▼────────────────────┐
                   │  stock.py                          │
                   │  charge le fichier Excel du stock  │
                   │  et retourne les lignes             │
                   │  correspondant aux noms choisis     │
                   └─────────────────────────────────────┘

                   kits.py / kits.json : kits de pièces validés,
                   réutilisés sans repartir de zéro à chaque fois
```

Aucun appel réseau externe : tout tourne en local (LM Studio héberge le
modèle de langage sur la machine).

---

## Prérequis

- Python 3.10+
- [LM Studio](https://lmstudio.ai) installé, avec un modèle de langage
  compatible chargé (le code est configuré pour `qwen3.5-4b` — voir plus
  bas pour changer le modèle)
- Un fichier Excel de stock (`stock.xlsx`) avec au minimum les colonnes :
  `ref`, `ref_fabricant`, `qte`, `emplacement`, `libele`

---

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

pip install streamlit pandas openpyxl requests rapidfuzz
```

| Paquet       | Utilisé pour                                              |
|--------------|-------------------------------------------------------------|
| `streamlit`  | Interface web                                                |
| `pandas`     | Lecture/écriture des fichiers Excel                          |
| `openpyxl`   | Moteur de lecture `.xlsx` utilisé par pandas                 |
| `requests`   | Appels HTTP vers l'API locale de LM Studio                   |
| `rapidfuzz`  | Recherche floue dans `kits.py` (fonction `rechercher_kit`, conservée mais non utilisée dans le flux principal actuel) |

> Le module `embeddings.py` (approche par similarité d'embeddings e5-large)
> a été **abandonné** au profit d'une correspondance directe faite par le
> LLM (`selectionner_references_pour_pieces`). Tu peux le supprimer du
> projet s'il traîne encore.

---

## Configuration de LM Studio

1. Ouvrir LM Studio → onglet **Local Server**.
2. Charger un modèle de chat (par défaut le code attend un modèle nommé
   `qwen3.5-4b` — adapte `MODEL` dans `llm.py` si tu utilises un autre modèle).
3. Démarrer le serveur local. Vérifier que l'URL et le chemin exposés
   correspondent à ceux configurés dans `llm.py` :

```python
LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"
MODEL = "qwen3.5-4b"
```

> ⚠️ Ce chemin (`/api/v1/chat`) et ce format de payload (`input`,
> `reasoning`, `store`, `max_output_tokens`) sont spécifiques à la
> configuration utilisée pour ce projet. Si ta version de LM Studio expose
> une API différente (par ex. `/v1/chat/completions` au format OpenAI
> classique), il faudra adapter `appeler_llm()` dans `llm.py` en
> conséquence.

Test rapide en ligne de commande pour vérifier que le serveur répond :

```bash
curl http://localhost:1234/api/v1/chat -d '{"model":"qwen3.5-4b","input":"dis bonjour"}'
```

---

## Pipeline de préparation des données

Le stock brut n'a pas de nom "propre" et unifié par produit — c'est ce que
cette chaîne de scripts construit, **à exécuter une fois** (ou à chaque
mise à jour significative du stock), **avant** de lancer l'application :

```
stock.xlsx
   │  (refs intactes)
   ▼
filtre_stock.py            regroupe les refs par "base" (avant le 1er chiffre)
   │                        et trie les lignes
   ▼
stock_filtre.xlsx
   │  (refs regroupées, ordre différent)
   ▼
create_name.py              groupe par ref filtrée, demande un nom
   │                        unifié au LLM pour chaque groupe
   ▼
named_stock.xlsx
   │  (refs regroupées + colonne nom_complet)
   ▼
fusionner_nom_complet.py    réinjecte nom_complet dans stock.xlsx via
   │                        une clé composite (ref_fabricant, qte,
   │                        emplacement, libele) — PAS via ref, puisque
   │                        ref a été transformée entre-temps
   ▼
stock_avec_nom_complet.xlsx  ← fichier à utiliser dans l'application
   │  (refs INTACTES + nom_complet)
   ▼
unique_named.py              extrait les nom_complet uniques, triés
   ▼
uniques_tries.txt            ← liste donnée à l'IA pour la mise en
                                correspondance des pièces recherchées
```

### Étapes en pratique

```bash
# 1. Regrouper/normaliser les références
python3 filtre_stock.py
# -> stock_filtre.xlsx

# 2. Générer un nom unifié par groupe de références (appelle le LLM,
#    peut prendre du temps selon le nombre de groupes)
python3 create_name.py
# -> named_stock.xlsx

# 3. Réinjecter nom_complet dans le stock original (refs intactes)
python3 fusionner_nom_complet.py
# -> stock_avec_nom_complet.xlsx
# Vérifie dans le terminal le nombre de lignes non appariées : si ce
# nombre est élevé, la clé composite n'est peut-être pas fiable pour ton
# fichier (voir section Dépannage).

# 4. Extraire la liste de noms uniques utilisée par l'IA en recherche
python3 unique_named.py
# -> uniques_tries.txt
# (à relancer si stock_avec_nom_complet.xlsx / named_stock.xlsx change)
```

> `unique_named.py` lit par défaut `named_stock.xlsx`. Comme ce fichier et
> `stock_avec_nom_complet.xlsx` ont exactement le même ensemble de valeurs
> `nom_complet` (seule la colonne `ref` diffère entre eux), la liste
> obtenue est identique quel que soit celui des deux qu'on lui donne — pas
> besoin de le modifier pour cette étape.

---

## Lancer l'application

```bash
streamlit run streamlitapp.py
```

L'app s'ouvre sur `http://localhost:8501`. Elle a besoin, dans le même
dossier :

- `stock_avec_nom_complet.xlsx` (voir l'avertissement en haut de ce README)
- `uniques_tries.txt`
- `kits.json`
- `.streamlit/config.toml` pour le thème (voir plus bas)

> **Thème Streamlit** : `config.toml` doit se trouver dans un sous-dossier
> `.streamlit/` à la racine du projet (`.streamlit/config.toml`), pas à la
> racine elle-même, sinon Streamlit ne l'applique pas.

### Ce qui se passe à chaque recherche

1. L'utilisateur saisit un besoin et valide (bouton ou touche Entrée).
2. `analyser_besoin_avec_kits()` envoie le besoin **+ la liste des kits
   connus** au LLM, qui répond soit avec un kit existant (`kit_choisi`),
   soit avec une nouvelle liste de pièces (`pieces`).
3. Si aucun kit ne convient : un bandeau propose d'enregistrer ce nouveau
   besoin comme kit pour la prochaine fois (`ajouter_kit`, dans `kits.py`).
4. `selectionner_references_pour_pieces()` envoie au LLM la liste des
   pièces identifiées **+ la liste complète des `nom_complet`** du stock
   (`uniques_tries.txt`), et récupère un mapping pièce → noms
   correspondants, classés par pertinence.
5. `stock.rechercher_par_noms()` récupère toutes les lignes du stock
   partageant ces `nom_complet`, avec un score reflétant le rang de
   pertinence donné par l'IA.
6. Résultats affichés en cartes (une par pièce), avec détail par référence
   au clic.

---

## Le système de kits

`kits.json` stocke des besoins types déjà validés, pour éviter de
ressolliciter le LLM (et garantir une liste de pièces cohérente) sur les
demandes récurrentes :

```json
{
  "kits": [
    {
      "id": "depart_moteur_triphase",
      "nom": "Départ moteur triphasé",
      "alias": ["demarrage moteur triphase", "depart moteur"],
      "pieces": ["moteur triphasé", "contacteur", "protection moteur", "relais thermique", "disjoncteur moteur"]
    }
  ]
}
```

- `charger_kits()` : lit `kits.json` (liste vide si le fichier n'existe pas encore).
- `ajouter_kit(nom, pieces, alias=...)` : ajoute/écrase un kit et
  sauvegarde — utilisé par le bouton "💾 Enregistrer ce besoin comme kit"
  dans l'interface.
- La sélection du kit le plus adapté à une demande est faite **par le LLM
  lui-même** (`analyser_besoin_avec_kits`), pas par recherche floue —
  `rechercher_kit()` reste disponible dans `kits.py` mais n'est plus
  appelée dans le flux principal.

Pour ajouter des kits manuellement, éditer directement `kits.json` (même
format que ci-dessus).

---

## Mode debug

`llm.py` contient un flag en haut du fichier :

```python
DEBUG = True
```

Quand il est actif, chaque appel au LLM affiche dans le terminal (pas
dans l'interface Streamlit) :

- le prompt envoyé,
- la réponse brute de LM Studio,
- le texte extrait du message,
- le JSON juste avant parsing,
- en cas d'échec du parsing JSON : l'erreur exacte + le texte brut reçu.

Utile pour diagnostiquer un JSON mal formé, tronqué, ou une réponse
inattendue du modèle. Repasser `DEBUG = False` avant un usage en
production pour ne pas polluer le terminal / les logs.

---

## Structure des fichiers

```
.
├── streamlitapp.py              # Interface principale (Streamlit)
├── llm.py                       # Appels LM Studio + logique d'analyse
├── stock.py                     # Chargement et recherche dans le stock
├── kits.py                      # Gestion des kits (charger/ajouter)
├── kits.json                    # Base des kits validés
├── .streamlit/
│   └── config.toml              # Thème Streamlit
│
├── filtre_stock.py              # Étape 1 du pipeline de données
├── create_name.py               # Étape 2 du pipeline de données
├── fusionner_nom_complet.py     # Étape 3 du pipeline de données
├── unique_named.py              # Étape 4 du pipeline de données
│
├── stock.xlsx                   # Stock brut (refs intactes) — à fournir
├── stock_filtre.xlsx            # Généré par filtre_stock.py
├── named_stock.xlsx             # Généré par create_name.py
├── stock_avec_nom_complet.xlsx  # Généré par fusionner_nom_complet.py — utilisé par l'app
└── uniques_tries.txt            # Généré par unique_named.py — utilisé par l'app
```

---

## Dépannage

**`Exception: Aucun message retourné par LM Studio`**
LM Studio ne répond pas au format attendu. Vérifier que le serveur local
est démarré, qu'un modèle est bien chargé, et que `LM_STUDIO_URL` /
`MODEL` dans `llm.py` correspondent à ta configuration.

**Erreur de parsing JSON (`json.decoder.JSONDecodeError`)**
Activer `DEBUG = True` dans `llm.py` : le terminal affichera le texte
brut renvoyé par le modèle. Cas fréquents : réponse tronquée (augmenter
`max_output_tokens` dans l'appel concerné), ou modèle qui ajoute du texte
avant/après le JSON malgré la consigne.

**Beaucoup de lignes "sans correspondance" après `fusionner_nom_complet.py`**
La clé composite (`ref_fabricant`, `qte`, `emplacement`, `libele`) n'est
peut-être pas assez stable pour ton fichier (une de ces colonnes a pu être
modifiée entre `stock.xlsx` et `named_stock.xlsx` par un autre traitement).
Regarder les exemples affichés dans le terminal pour identifier la colonne
en cause, puis ajuster `COLONNES_CLE` dans `fusionner_nom_complet.py`.

**Le LLM ne trouve pas de bonnes correspondances dans `selectionner_references_pour_pieces`**
Si `uniques_tries.txt` contient plusieurs centaines/milliers de lignes, le
prompt peut dépasser la fenêtre de contexte du modèle local, provoquant
des réponses tronquées ou incomplètes. Solutions possibles : découper la
liste de noms en lots plus petits et faire plusieurs appels, ou
pré-filtrer grossièrement (mots-clés) avant de solliciter le LLM.

**Les cartes de composants s'affichent en HTML brut (texte au lieu du rendu)**
Vérifier que le HTML passé à `st.markdown()` est bien débarrassé de son
indentation via `textwrap.dedent(...).strip()` avant l'appel — Markdown
traite tout bloc indenté de 4+ espaces comme du code.

**La recherche ne se déclenche pas avec la touche Entrée**
Le champ de recherche doit être à l'intérieur d'un `st.form(...)` avec un
`st.form_submit_button(...)` — un `st.text_input` + `st.button` séparés ne
réagissent pas à la touche Entrée.
