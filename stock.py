import pandas as pd
from rapidfuzz import fuzz


class Stock:


    def __init__(self, fichier):

        self.df = pd.read_excel(fichier)


        colonnes = [
            "ref",
            "ref_fabricant",
            "qte",
            "emplacement",
            "libele"
        ]


        self.df = self.df[colonnes]


        self.df = self.df.fillna("")



    def score(self, besoin, ligne):


        texte = (
            str(ligne["ref"])
            +" "
            +str(ligne["ref_fabricant"])
            +" "
            +str(ligne["libele"])
        )


        return fuzz.partial_ratio(
            besoin.lower(),
            texte.lower()
        )



    def rechercher(
            self,
            besoin,
            limite=25
    ):


        resultats=[]


        for _, ligne in self.df.iterrows():


            score = self.score(
                besoin,
                ligne
            )


            if score >= 40:


                resultats.append({

                    "besoin": besoin,

                    "reference":
                        ligne["ref"],

                    "fabricant":
                        ligne["ref_fabricant"],

                    "quantite":
                        int(ligne["qte"]),

                    "emplacement":
                        ligne["emplacement"],

                    "libele":
                        ligne["libele"],

                    "score":
                        round(score,1)
                })



        resultats.sort(
            key=lambda x:x["score"],
            reverse=True
        )


        return resultats[:limite]