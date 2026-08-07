import numpy as np
from sentence_transformers import SentenceTransformer


# Modèle e5-large : téléchargé automatiquement depuis Hugging Face lors
# du premier lancement (~1.3 Go), puis mis en cache localement
# (dossier ~/.cache/huggingface) pour les exécutions suivantes.
NOM_MODELE = "intfloat/e5-large-v2"


# Le modèle est chargé une seule fois par processus (variable de module),
# pour éviter de le recharger à chaque appel de fonction.
_modele = None


def _charger_modele():

    global _modele

    if _modele is None:
        _modele = SentenceTransformer(NOM_MODELE)

    return _modele


def texte_requete(texte):
    """
    Les modèles E5 sont entraînés avec des préfixes distincts pour les
    requêtes et les documents. On préfixe donc le besoin utilisateur
    par "query: " avant de l'encoder.
    """
    return f"query: {texte}"


def texte_passage(texte):
    """
    De même, chaque texte de la base (ici les 'nom_complet' du stock)
    doit être préfixé par "passage: " avant d'être encodé.
    """
    return f"passage: {texte}"


def obtenir_embeddings(textes):
    """
    Encode une liste de textes en une seule fois (plus rapide que
    texte par texte) et retourne la liste des vecteurs correspondants.
    Les vecteurs sont normalisés, donc leur produit scalaire équivaut
    directement à une similarité cosinus.
    """

    modele = _charger_modele()

    vecteurs = modele.encode(
        textes,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return vecteurs.tolist()


def obtenir_embedding(texte):
    """
    Variante pratique pour obtenir l'embedding d'un seul texte.
    """
    return obtenir_embeddings([texte])[0]


def similarite_cosinus(vecteur_a, vecteur_b):

    a = np.asarray(vecteur_a, dtype=float)
    b = np.asarray(vecteur_b, dtype=float)

    norme_a = np.linalg.norm(a)
    norme_b = np.linalg.norm(b)

    if norme_a == 0 or norme_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norme_a * norme_b))
