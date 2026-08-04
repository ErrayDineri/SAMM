import requests
import json


URL = "http://localhost:1234/api/v1/chat"

MODEL = "qwen3.5-4b"



def appel_lm(payload):


    response = requests.post(
        URL,
        json=payload,
        timeout=120
    )


    data = response.json()


    if "error" in data:

        raise Exception(
            data["error"]["message"]
        )


    return data





def extraire_message(data):


    for item in data["output"]:

        if item["type"] == "message":

            return item["content"]


    raise Exception(
        "Aucun message trouvé"
    )






def analyser_besoin(question):


    prompt = f"""

Tu es un expert en nomenclature électrique industrielle.


Analyse le besoin utilisateur.

Détermine uniquement les familles de composants nécessaires.

Catégories autorisées :

- contacteur
- disjoncteur
- relais thermique
- moteur
- cable
- boitier
- variateur


Ne montre aucun raisonnement.

Retourne uniquement du JSON valide.


Format :

{{
 "pieces":[]
}}



Demande :

{question}

"""


    data = appel_lm({

        "model": MODEL,

        "input": prompt,

        "temperature": 0,

        "reasoning": "off",

        "stream": False

    })


    texte = extraire_message(data)


    return json.loads(texte)["pieces"]






def generer_reponse(question, composants):


    prompt = f"""

Tu es un assistant industriel.


Demande :

{question}


Voici les composants disponibles :

{json.dumps(
    composants,
    indent=2,
    ensure_ascii=False
)}



Retourne uniquement un JSON.


Format obligatoire :


{{
 "demande":"",
 "composants":[]
}}


"""


    data = appel_lm({

        "model": MODEL,

        "input": prompt,

        "temperature":0,

        "reasoning":"off",

        "stream":False

    })


    texte = extraire_message(data)


    return json.loads(texte)