import json
import requests


LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"

MODEL = "qwen3.5-4b"


# Mettre à False pour couper l'affichage de debug dans le terminal.
DEBUG = True


def _debug(titre, contenu):

    if not DEBUG:
        return

    print("\n" + "=" * 70)
    print(f"[DEBUG] {titre}")
    print("=" * 70)
    print(contenu)
    print("=" * 70 + "\n")


def appeler_llm(prompt, max_output_tokens=300):

    _debug("PROMPT ENVOYÉ AU LLM", prompt)

    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": MODEL,
            "input": prompt,
            "temperature": 0,
            "reasoning": "off",
            "stream": False,
            "store": False,
            "max_output_tokens": max_output_tokens
        },
        timeout=120
    )

    data = response.json()

    _debug(
        "RÉPONSE BRUTE DE LM STUDIO",
        json.dumps(data, indent=2, ensure_ascii=False)
    )

    if "error" in data:
        raise Exception(
            data["error"]["message"]
        )

    return data



def extraire_message(data):

    for item in data.get("output", []):

        if item.get("type") == "message":

            _debug("TEXTE EXTRAIT DU MESSAGE", item["content"])

            return item["content"]

    raise Exception(
        "Aucun message retourné par LM Studio"
    )



def _parser_json(texte, contexte=""):
    """
    Nettoie et parse le JSON renvoyé par le LLM. En cas d'échec, affiche
    le texte brut reçu dans le terminal avant de relancer l'erreur, pour
    faciliter le débogage (JSON tronqué, mal formé, texte parasite...).
    """

    texte_nettoye = (
        texte
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    _debug(
        f"JSON À PARSER{' (' + contexte + ')' if contexte else ''}",
        texte_nettoye
    )

    try:
        return json.loads(texte_nettoye)

    except json.JSONDecodeError as erreur:

        _debug(
            "ÉCHEC DU PARSING JSON",
            f"Erreur : {erreur}\n\nTexte reçu :\n{texte_nettoye}"
        )

        raise



def analyser_besoin(question):

    prompt = f"""

Tu es un expert en conception électrique industrielle.

Analyse la demande utilisateur.

Ton rôle est uniquement d'identifier les familles
de composants nécessaires.

Ne donne aucune référence.
Ne donne aucune quantité.
Ne donne aucune explication.

Retourne uniquement du JSON valide.

Format :

{{
 "pieces": [
    "composant 1",
    "composant 2"
 ]
}}


Exemples :

Demande :
Créer un départ moteur triphasé.

Réponse :

{{
 "pieces":[
    "moteur triphasé",
    "contacteur",
    "protection moteur",
    "relais thermique"
 ]
}}


Demande :
Créer une armoire électrique automatique.

Réponse :

{{
 "pieces":[
    "automate",
    "alimentation 24V",
    "relais interface",
    "bornier",
    "disjoncteur"
 ]
}}


Demande utilisateur :

{question}

"""


    data = appeler_llm(prompt)


    texte = extraire_message(data)


    resultat = _parser_json(texte, contexte="analyser_besoin")


    return resultat["pieces"]



def _decrire_kits(kits):
    """
    Construit un texte listant les kits connus (id, nom, pièces),
    à insérer dans le prompt pour que l'IA puisse en choisir un.
    """

    if not kits:
        return "(aucun kit connu pour le moment)"

    lignes = []

    for kit in kits:

        pieces_txt = ", ".join(kit.get("pieces", []))

        lignes.append(
            f'- id: "{kit["id"]}" | nom: "{kit["nom"]}" | '
            f'pieces habituelles: [{pieces_txt}]'
        )

    return "\n".join(lignes)



def analyser_besoin_avec_kits(question, kits):
    """
    Comme analyser_besoin, mais l'IA a d'abord connaissance des kits
    déjà validés. Si un kit correspond clairement au besoin, elle
    renvoie son id (kit_choisi) sans repartir de zéro. Sinon, elle
    propose directement la liste des familles de composants (pieces),
    comme pour un besoin inédit.

    Retourne un tuple (kit_choisi, pieces) :
    - kit_choisi : id du kit (str) ou None
    - pieces : liste de composants (utile seulement si kit_choisi est None)
    """

    kits_texte = _decrire_kits(kits)

    prompt = f"""

Tu es un expert en conception électrique industrielle.

Voici les kits déjà connus et validés, chacun correspondant à un besoin
type et à une liste de pièces habituelles :

{kits_texte}

Analyse la demande utilisateur ci-dessous.

Si un de ces kits correspond clairement au besoin exprimé, réponds avec
son id exact dans "kit_choisi" et laisse "pieces" vide.

Si aucun kit ne correspond de façon convaincante (besoin différent,
incomplet, ou trop spécifique), réponds avec "kit_choisi": null et
donne dans "pieces" la liste des familles de composants nécessaires.
Ne donne aucune référence, aucune quantité, aucune explication dans
"pieces".

Retourne uniquement du JSON valide, au format :

{{
 "kit_choisi": "id_du_kit_ou_null",
 "pieces": ["composant 1", "composant 2"]
}}

Demande utilisateur :

{question}

"""

    data = appeler_llm(prompt)

    texte = extraire_message(data)

    resultat = _parser_json(texte, contexte="analyser_besoin_avec_kits")

    kit_choisi = resultat.get("kit_choisi")

    # Certains modèles renvoient la chaîne "null" plutôt que le
    # littéral JSON null : on normalise les deux cas.
    if kit_choisi in (None, "null", ""):
        kit_choisi = None

    pieces = resultat.get("pieces", [])

    _debug(
        "RÉSULTAT analyser_besoin_avec_kits",
        f"kit_choisi = {kit_choisi}\npieces = {pieces}"
    )

    return kit_choisi, pieces



def _decrire_pieces(pieces):

    return "\n".join(
        f'- "{piece}"'
        for piece in pieces
    )



def selectionner_references_pour_pieces(pieces, noms_complets):
    """
    Demande à l'IA de faire correspondre chaque pièce identifiée à un
    ou plusieurs noms de produits existant réellement dans le stock
    (colonne "nom_complet"), plutôt que de comparer des vecteurs
    d'embedding.

    Retourne un dict : { piece: [nom_le_plus_pertinent, ...], ... }
    Les listes de noms sont classées du plus pertinent au moins
    pertinent ; une liste vide signifie qu'aucun nom ne correspond.

    NOTE : si le catalogue de noms est très volumineux (plusieurs
    centaines/milliers de lignes), le prompt peut dépasser la fenêtre
    de contexte du modèle local. Dans ce cas, il faudra pré-filtrer ou
    découper la liste de noms avant de l'envoyer (par lots), plutôt
    que de tout envoyer en un seul appel comme ici.
    """

    if not pieces:
        return {}

    noms_texte = "\n".join(
        f"- {nom}"
        for nom in noms_complets
    )

    pieces_texte = _decrire_pieces(pieces)

    prompt = f"""

Tu es un expert en composants électriques et en automatisme industriel.

Voici la liste EXACTE des noms de produits disponibles en stock (un par
ligne) :

{noms_texte}

Voici la liste des composants recherchés :

{pieces_texte}

Pour CHAQUE composant recherché, identifie parmi la liste de noms
ci-dessus ceux qui correspondent le mieux. Recopie les noms EXACTEMENT
tels qu'ils apparaissent dans la liste, sans les modifier ni en
inventer de nouveaux qui n'y figurent pas. Classe-les du plus pertinent
au moins pertinent. Si aucun nom ne correspond à un composant, laisse
une liste vide pour celui-ci.

Retourne uniquement du JSON valide, au format :

{{
 "correspondances": {{
    "nom du composant 1": ["nom le plus pertinent", "nom suivant"],
    "nom du composant 2": []
 }}
}}

"""

    data = appeler_llm(prompt, max_output_tokens=900)

    texte = extraire_message(data)

    texte = (
        texte
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    resultat = json.loads(texte)

    return resultat.get("correspondances", {})