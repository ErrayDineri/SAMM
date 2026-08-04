import json
from typing import Any

import requests


LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"

# Nom exact du modèle téléchargé dans LM Studio.
MODEL = "qwen3.5-4b"

CATEGORIES_AUTORISEES = {
    "contacteur",
    "contact auxiliaire",
    "disjoncteur",
    "disjoncteur moteur",
    "relais",
    "relais thermique",
    "sectionneur",
    "connecteur",
    "moteur",
    "cable",
    "boitier",
    "variateur",
}


def appeler_lm_studio(payload: dict[str, Any]) -> dict[str, Any]:
    """Envoie une requête non streamée à l'API native de LM Studio."""

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

    except requests.ConnectionError as exc:
        raise RuntimeError(
            "Impossible de joindre LM Studio. "
            "Vérifie que le serveur local est lancé sur le port 1234."
        ) from exc

    except requests.Timeout as exc:
        raise RuntimeError(
            "LM Studio n'a pas répondu dans le délai imparti."
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Erreur HTTP pendant l'appel à LM Studio : {exc}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"LM Studio a retourné une réponse non JSON : {response.text}"
        ) from exc

    if "error" in data:
        erreur = data["error"]
        message = erreur.get("message", str(erreur))

        raise RuntimeError(f"Erreur LM Studio : {message}")

    return data


def extraire_message(data: dict[str, Any]) -> str:
    """Récupère uniquement le contenu de type message, sans le reasoning."""

    output = data.get("output")

    if not isinstance(output, list):
        raise RuntimeError(
            "La réponse LM Studio ne contient pas de champ 'output' valide."
        )

    for item in output:
        if (
            isinstance(item, dict)
            and item.get("type") == "message"
            and isinstance(item.get("content"), str)
        ):
            return item["content"].strip()

    raise RuntimeError(
        "Aucun message final n'a été trouvé dans la réponse LM Studio."
    )


def nettoyer_json(texte: str) -> str:
    """Retire éventuellement les balises Markdown autour du JSON."""

    texte = texte.strip()

    if texte.startswith("```json"):
        texte = texte[len("```json"):].strip()
    elif texte.startswith("```"):
        texte = texte[len("```"):].strip()

    if texte.endswith("```"):
        texte = texte[:-3].strip()

    return texte


def analyser_besoin(question: str) -> list[str]:
    """
    Transforme une demande utilisateur en familles de composants électriques.
    Le LLM ne consulte pas le stock et ne sélectionne aucune référence.
    """

    prompt = f"""
Tu es un moteur d'analyse de nomenclature électrique industrielle.

Ta seule tâche est d'identifier les familles de composants nécessaires
pour répondre à la demande utilisateur.

Règles obligatoires :

- Retourne uniquement un objet JSON valide.
- Ne donne aucune explication.
- Ne montre pas ton raisonnement.
- Ne retourne aucune référence fabricant.
- Ne retourne jamais de quantité.
- Ne retourne pas le montage demandé comme composant.
- N'utilise que les catégories autorisées ci-dessous.
- N'ajoute pas de catégorie incertaine.

Catégories autorisées :

- contacteur
- contact auxiliaire
- disjoncteur
- disjoncteur moteur
- relais
- relais thermique
- sectionneur
- connecteur
- moteur
- cable
- boitier
- variateur

Exemple :

Demande :
Créer un coffret de démarrage direct pour un moteur triphasé.

Réponse :
{{
  "pieces": [
    "contacteur",
    "disjoncteur moteur",
    "relais thermique",
    "boitier"
  ]
}}

Format obligatoire :

{{
  "pieces": []
}}

Demande utilisateur :

{question}
""".strip()

    data = appeler_lm_studio(
        {
            "model": MODEL,
            "input": prompt,
            "temperature": 0,
            "reasoning": "off",
            "stream": False,
            "store": False,
            "max_output_tokens": 300,
        }
    )

    texte = nettoyer_json(extraire_message(data))

    try:
        resultat = json.loads(texte)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Le modèle n'a pas retourné un JSON valide.\n"
            f"Réponse reçue :\n{texte}"
        ) from exc

    pieces = resultat.get("pieces")

    if not isinstance(pieces, list):
        raise RuntimeError(
            "Le JSON retourné doit contenir une liste nommée 'pieces'."
        )

    pieces_nettoyees: list[str] = []

    for piece in pieces:
        if not isinstance(piece, str):
            continue

        piece = piece.strip().lower()

        if piece in CATEGORIES_AUTORISEES and piece not in pieces_nettoyees:
            pieces_nettoyees.append(piece)

    return pieces_nettoyees