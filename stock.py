import os

import pandas as pd


FICHIER_NOMS_UNIQUES = "uniques_tries.txt"


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


    def _quantite(self, valeur):

        try:
            return int(valeur)
        except (ValueError, TypeError):
            return 0


    def noms_complets_uniques(self, fichier=FICHIER_NOMS_UNIQUES):
        """
        Retourne la liste des noms de produits uniques ("nom_complet")
        à proposer à l'IA pour la mise en correspondance.

        Si un fichier pré-généré existe (ex: uniques_tries.txt, une
        liste déjà déduplicable et triée), on l'utilise en priorité :
        cela garantit la cohérence avec un éventuel nettoyage externe
        des libellés. Sinon, on déduit la liste directement du stock
        chargé en mémoire.
        """

        if os.path.exists(fichier):

            with open(fichier, "r", encoding="utf-8") as f:
                noms = [
                    ligne.strip()
                    for ligne in f
                    if ligne.strip()
                ]

            if noms:
                return noms

        noms = sorted(set(
            str(nom).strip()
            for nom in self.df["nom_complet"]
            if str(nom).strip()
        ))

        return noms


    def rechercher_par_noms(self, besoin, noms_choisis, limite=None):
        """
        Retourne toutes les lignes du stock dont le "nom_complet"
        correspond à l'un des noms choisis par l'IA pour ce besoin,
        en respectant l'ordre de pertinence qu'elle a donné (le champ
        "score" reflète ce rang, pas une mesure de similarité
        mathématique comme avec les embeddings).
        """

        if not noms_choisis:
            return []

        rang_par_nom = {
            nom.strip().lower(): index
            for index, nom in enumerate(noms_choisis)
        }

        resultats = []

        for _, ligne in self.df.iterrows():

            nom_ligne = str(ligne["nom_complet"]).strip().lower()

            if nom_ligne in rang_par_nom:

                rang = rang_par_nom[nom_ligne]

                # Score décroissant selon le rang de pertinence donné
                # par l'IA (100 pour le choix le plus pertinent, puis
                # -10 par rang, avec un plancher à 10).
                score = max(100 - rang * 10, 10)

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
                        score
                })


        resultats.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        if limite is not None:
            return resultats[:limite]

        return resultats