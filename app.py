from stock import Stock
from llm import analyser_besoin, generer_reponse

import json



stock = Stock(
    "stock.xlsx"
)



print("======================")
print(" SAMM STOCK AI ")
print("======================")



while True:


    question = input(
        "\nBesoin : "
    )


    if question.lower() == "exit":

        break



    print(
        "\nAnalyse...\n"
    )


    try:

        pieces = analyser_besoin(
            question
        )


        print(
            "Pièces nécessaires :",
            pieces
        )


    except Exception as e:

        print(
            "Erreur LLM :",
            e
        )

        continue



    composants = []



    for piece in pieces:


        composants.extend(

            stock.rechercher(
                piece
            )

        )



    print(
        "\nGénération JSON...\n"
    )



    resultat = generer_reponse(

        question,

        composants

    )



    print(
        json.dumps(
            resultat,
            indent=2,
            ensure_ascii=False
        )
    )