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