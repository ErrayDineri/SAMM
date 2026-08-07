import hashlib
import os

import numpy as np
import pandas as pd

from embeddings import (
    obtenir_embeddings,
    obtenir_embedding,
    similarite_cosinus,
    texte_requete,
    texte_passage
)


FICHIER_CACHE_EMBEDDINGS = "embeddings_cache.npz"


class Stock:

    def __init__(self, fichier):

        self.df = pd.read_excel(fichier)

        colonnes = [
            "ref",
            "ref_fabricant",
            "qte",
            "emplacement",
            "libele",
            "nom_complet"
        ]

        self.df = self.df[colonnes]
        self.df = self.df.fillna("")

        self.embeddings = self._charger_ou_calculer_embeddings()


    def _empreinte_donnees(self):
        """
        Calcule une empreinte du contenu (ref + nom_complet) afin de
        savoir si le cache d'embeddings est encore valide, ou si le
        fichier de stock a changé depuis le dernier calcul (auquel cas
        il faut recalculer les embeddings).
        """

        contenu = "".join(
            f"{ref}|{nom}"
            for ref, nom in zip(
                self.df["ref"],
                self.df["nom_complet"]
            )
        )

        return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


    def _charger_ou_calculer_embeddings(self):

        empreinte = self._empreinte_donnees()

        if os.path.exists(FICHIER_CACHE_EMBEDDINGS):

            cache = np.load(FICHIER_CACHE_EMBEDDINGS, allow_pickle=True)

            if str(cache["empreinte"]) == empreinte:
                return cache["embeddings"]

        # Cache absent ou périmé : on encode tous les "nom_complet"
        # avec le modèle e5-large (calcul local, peut prendre du temps
        # selon la taille du stock, mais ne se refait qu'une fois).
        textes = [
            texte_passage(nom)
            for nom in self.df["nom_complet"]
        ]

        vecteurs = np.array(
            obtenir_embeddings(textes)
        )

        np.savez(
            FICHIER_CACHE_EMBEDDINGS,
            embeddings=vecteurs,
            empreinte=empreinte
        )

        return vecteurs


    def _quantite(self, valeur):

        try:
            return int(valeur)
        except (ValueError, TypeError):
            return 0


    def rechercher(self, besoin, limite=None, seuil=0.80):
        """
        Recherche les references du stock dont le "nom_complet" est
        semantiquement proche du besoin, via similarite cosinus entre
        embeddings e5-large (au lieu d'une correspondance de caracteres).

        Le seuil est a calibrer avec des donnees reelles : les scores de
        similarite e5 sont generalement plus resserres qu'un score de
        correspondance de texte (ex : 0.75-0.95 pour des elements lies).
        """

        vecteur_besoin = np.array(
            obtenir_embedding(
                texte_requete(besoin)
            )
        )

        resultats = []

        for index, ligne in self.df.iterrows():

            score = similarite_cosinus(
                vecteur_besoin,
                self.embeddings[index]
            )

            if score >= seuil:

                resultats.append({

                    "besoin": besoin,

                    "reference":
                        ligne["ref"],

                    "fabricant":
                        ligne["ref_fabricant"],

                    "quantite":
                        self._quantite(ligne["qte"]),

                    "emplacement":
                        ligne["emplacement"],

                    "libele":
                        ligne["libele"],

                    "nom_complet":
                        ligne["nom_complet"],

                    "score":
                        round(score * 100, 1)
                })


        resultats.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        if limite is not None:
            return resultats[:limite]

        return resultats