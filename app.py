import json
from pathlib import Path
from typing import Any

from llm import analyser_besoin
from stock import Stock


DOSSIER_PROJET = Path(__file__).resolve().parent
FICHIER_STOCK = DOSSIER_PROJET / "stockfinal.xlsx"


def construire_resultat(
    question: str,
    familles: list[str],
    stock: Stock,
) -> dict[str, Any]:
    """
    Construit directement le JSON final avec Python.
    Aucun deuxième appel au LLM n'est effectué.
    """

    composants: list[dict[str, Any]] = []

    for famille in familles:
        correspondances = stock.rechercher(
            besoin=famille,
            seuil=65,
            limite=5,
        )

        composants.append(
            {
                "besoin": famille,
                "resultats": correspondances,
            }
        )

    return {
        "demande": question,
        "pieces_recherchees": familles,
        "composants": composants,
    }


def main() -> None:
    try:
        stock = Stock(FICHIER_STOCK)
    except Exception as exc:
        print(f"Erreur lors du chargement du stock : {exc}")
        return

    print("=" * 40)
    print(" SAMM — Recherche de composants")
    print("=" * 40)
    print("Tapez 'exit' pour quitter.")

    while True:
        question = input("\nBesoin : ").strip()

        if question.lower() in {
            "exit",
            "quit",
            "stop",
        }:
            print("Fermeture de SAMM.")
            break

        if not question:
            print("Veuillez saisir un besoin.")
            continue

        print("\nAnalyse du besoin...")

        try:
            familles = analyser_besoin(question)
        except Exception as exc:
            print(f"Erreur pendant l'analyse : {exc}")
            continue

        resultat = construire_resultat(
            question=question,
            familles=familles,
            stock=stock,
        )

        print("\nRésultat JSON :\n")

        print(
            json.dumps(
                resultat,
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()