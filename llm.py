import json
import requests


LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"

MODEL = "qwen3.5-4b"


def appeler_llm(prompt):

    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": MODEL,
            "input": prompt,
            "temperature": 0,
            "reasoning": "off",
            "stream": False,
            "store": False,
            "max_output_tokens": 300
        },
        timeout=120
    )

    data = response.json()

    if "error" in data:
        raise Exception(
            data["error"]["message"]
        )

    return data



def extraire_message(data):

    for item in data.get("output", []):

        if item.get("type") == "message":
            return item["content"]

    raise Exception(
        "Aucun message retourné par LM Studio"
    )



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


    texte = (
        texte
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )


    resultat = json.loads(texte)


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

    texte = (
        texte
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    resultat = json.loads(texte)

    kit_choisi = resultat.get("kit_choisi")

    # Certains modèles renvoient la chaîne "null" plutôt que le
    # littéral JSON null : on normalise les deux cas.
    if kit_choisi in (None, "null", ""):
        kit_choisi = None

    pieces = resultat.get("pieces", [])

    return kit_choisi, pieces