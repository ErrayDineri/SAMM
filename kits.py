import json
import os

from rapidfuzz import fuzz


FICHIER_KITS_DEFAUT = "kits.json"


def charger_kits(fichier=FICHIER_KITS_DEFAUT):
    """
    Charge la liste des kits depuis le fichier JSON.
    Si le fichier n'existe pas encore, retourne une liste vide
    au lieu de planter (premier lancement de l'application).
    """

    if not os.path.exists(fichier):
        return []

    with open(fichier, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("kits", [])



def sauvegarder_kits(kits, fichier=FICHIER_KITS_DEFAUT):

    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(
            {"kits": kits},
            f,
            ensure_ascii=False,
            indent=2
        )



def _libelles_kit(kit):
    """
    Retourne tous les libellés associés à un kit (son nom + ses
    alias), utilisés comme candidats pour la recherche floue.
    """

    return [kit["nom"]] + kit.get("alias", [])



def rechercher_kit(question, kits, seuil=75):
    """
    Cherche, parmi les kits connus, celui dont le nom ou un alias
    correspond le mieux à la question posée.

    Retourne le kit trouvé (dict) si son score de similarité dépasse
    le seuil, sinon None (dans ce cas, on retombera sur l'IA pour
    analyser un besoin inédit).
    """

    meilleur_kit = None
    meilleur_score = 0

    for kit in kits:

        for libelle in _libelles_kit(kit):

            score = fuzz.token_sort_ratio(
                question.lower().strip(),
                libelle.lower().strip()
            )

            if score > meilleur_score:
                meilleur_score = score
                meilleur_kit = kit

    if meilleur_score >= seuil:
        return meilleur_kit

    return None



def ajouter_kit(nom, pieces, fichier=FICHIER_KITS_DEFAUT, alias=None):
    """
    Enregistre un nouveau kit (typiquement un besoin identifié par
    l'IA, validé par l'utilisateur) afin qu'il soit reconnu
    instantanément lors d'une prochaine demande similaire.
    """

    kits = charger_kits(fichier)

    nouvel_id = (
        nom.lower()
        .strip()
        .replace(" ", "_")
    )

    # Évite les doublons si un kit avec le même id existe déjà :
    # on remplace plutôt que d'empiler des entrées identiques.
    kits = [k for k in kits if k.get("id") != nouvel_id]

    kits.append({
        "id": nouvel_id,
        "nom": nom,
        "alias": alias or [],
        "pieces": pieces
    })

    sauvegarder_kits(kits, fichier)

    return kits