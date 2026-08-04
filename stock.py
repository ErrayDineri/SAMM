from pathlib import Path
from typing import Any

import pandas as pd
from rapidfuzz import fuzz


COLONNES_OBLIGATOIRES = {
    "ref",
    "ref_fabricant",
    "qte",
    "emplacement",
    "libele",
}


SYNONYMES = {
    "contacteur": [
        "contacteur",
        "lc1d",
        "lc1",
        "tesys",
    ],
    "contact auxiliaire": [
        "contact auxiliaire",
        "contact inverseur",
        "1no",
        "1nc",
        "1o+1f",
        "gvan",
    ],
    "disjoncteur": [
        "disjoncteur",
        "ic60",
        "c60",
        "acti9",
        "dt40",
    ],
    "disjoncteur moteur": [
        "disjoncteur moteur",
        "protection moteur",
        "gv2",
        "gv3",
    ],
    "relais": [
        "relais",
        "finder",
        "rxm",
    ],
    "relais thermique": [
        "relais thermique",
        "protection thermique",
        "relais de surcharge",
        "overload relay",
    ],
    "sectionneur": [
        "sectionneur",
        "interrupteur sectionneur",
    ],
    "connecteur": [
        "connecteur",
        "connecteurs",
        "m12",
        "odu",
    ],
    "moteur": [
        "moteur",
        "motor",
    ],
    "cable": [
        "cable",
        "câble",
        "conducteur",
        "fil électrique",
    ],
    "boitier": [
        "boitier",
        "boîtier",
        "coffret",
        "armoire",
        "enclosure",
    ],
    "variateur": [
        "variateur",
        "variateur de vitesse",
        "frequency inverter",
        "vfd",
        "drive",
        "altivar",
    ],
}


PREFIXES_REFERENCE = {
    "contacteur": ("CONTACT",),
    "contact auxiliaire": ("CONTACT",),
    "disjoncteur": ("DISJ",),
    "disjoncteur moteur": ("DISJ",),
    "relais": ("RELAI",),
    "relais thermique": ("RELAI",),
    "sectionneur": ("SECT",),
    "connecteur": ("CONN",),
    "moteur": ("MOT", "MOTEUR"),
}


class Stock:
    def __init__(self, fichier: str | Path):
        chemin = Path(fichier)

        if not chemin.exists():
            raise FileNotFoundError(
                f"Le fichier Excel est introuvable : {chemin.resolve()}"
            )

        self.df = pd.read_excel(chemin)

        colonnes_manquantes = COLONNES_OBLIGATOIRES - set(self.df.columns)

        if colonnes_manquantes:
            raise ValueError(
                "Colonnes manquantes dans le fichier Excel : "
                + ", ".join(sorted(colonnes_manquantes))
            )

        self.df = self.df[
            [
                "ref",
                "ref_fabricant",
                "qte",
                "emplacement",
                "libele",
            ]
        ].copy()

        for colonne in [
            "ref",
            "ref_fabricant",
            "emplacement",
            "libele",
        ]:
            self.df[colonne] = (
                self.df[colonne]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        self.df["qte"] = (
            pd.to_numeric(self.df["qte"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    @staticmethod
    def _normaliser(texte: Any) -> str:
        return str(texte).strip().lower()

    def _calculer_score(
        self,
        besoin: str,
        ligne: pd.Series,
    ) -> float:
        termes = SYNONYMES.get(besoin, [besoin])

        ref = self._normaliser(ligne["ref"])
        ref_fabricant = self._normaliser(ligne["ref_fabricant"])
        libelle = self._normaliser(ligne["libele"])

        meilleur_score = 0.0

        for terme in termes:
            terme = self._normaliser(terme)

            score_libelle = fuzz.partial_ratio(terme, libelle)
            score_fabricant = fuzz.partial_ratio(
                terme,
                ref_fabricant,
            )

            score = (
                score_libelle * 0.85
                + score_fabricant * 0.15
            )

            meilleur_score = max(meilleur_score, score)

        prefixes = PREFIXES_REFERENCE.get(besoin, ())

        if prefixes and ref.upper().startswith(prefixes):
            meilleur_score += 15

        return min(meilleur_score, 100.0)

    def rechercher(
        self,
        besoin: str,
        seuil: float = 65,
        limite: int = 5,
    ) -> list[dict[str, Any]]:
        besoin_normalise = self._normaliser(besoin)

        resultats: list[dict[str, Any]] = []

        for _, ligne in self.df.iterrows():
            if ligne["qte"] <= 0:
                continue

            score = self._calculer_score(
                besoin_normalise,
                ligne,
            )

            if score < seuil:
                continue

            resultats.append(
                {
                    "besoin": besoin_normalise,
                    "reference": ligne["ref"],
                    "reference_fabricant": ligne[
                        "ref_fabricant"
                    ],
                    "quantite": int(ligne["qte"]),
                    "emplacement": ligne["emplacement"],
                    "libelle": ligne["libele"],
                    "score": round(score, 2),
                }
            )

        resultats.sort(
            key=lambda element: (
                element["score"],
                element["quantite"],
            ),
            reverse=True,
        )

        return resultats[:limite]