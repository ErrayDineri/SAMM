import pandas as pd
from rapidfuzz import fuzz


SYNONYMES = {

    "contacteur": [
        "contacteur",
        "lc1",
        "tesys"
    ],

    "disjoncteur": [
        "disjoncteur",
        "ic60",
        "gv2",
        "c60"
    ],

    "relais thermique": [
        "relais thermique",
        "relais",
        "protection moteur"
    ],

    "moteur": [
        "moteur",
        "motor"
    ],

    "cable": [
        "cable",
        "câble",
        "fil"
    ],

    "boitier": [
        "boitier",
        "coffret",
        "armoire"
    ],

    "variateur": [
        "variateur",
        "drive",
        "vfd"
    ]

}



class Stock:


    def __init__(self, fichier):

        self.df = pd.read_excel(fichier)

        self.df.columns = [
            "ref",
            "ref_fabricant",
            "qte",
            "emplacement",
            "libele"
        ]



    def rechercher(self, besoin, seuil=55):


        termes = SYNONYMES.get(
            besoin.lower(),
            [besoin]
        )


        resultats = []


        for _, ligne in self.df.iterrows():


            texte = (

                str(ligne["libele"])
                + " "
                + str(ligne["libele"])
                + " "
                + str(ligne["ref_fabricant"])

            ).lower()



            meilleur_score = 0


            for terme in termes:

                score = fuzz.partial_ratio(
                    terme.lower(),
                    texte
                )

                meilleur_score = max(
                    meilleur_score,
                    score
                )



            if meilleur_score >= seuil:


                resultats.append({

                    "besoin": besoin,

                    "reference": ligne["ref"],

                    "fabricant": ligne["ref_fabricant"],

                    "quantite": int(ligne["qte"]),

                    "emplacement": ligne["emplacement"],

                    "libele": ligne["libele"],

                    "score": meilleur_score

                })



        resultats.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        return resultats[:5]