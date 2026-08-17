import pandas as pd


FICHIER_STOCK_ORIGINAL = "stock.xlsx"        # refs intactes, source de vérité
FICHIER_STOCK_NOMME = "named_stock.xlsx"     # contient nom_complet, mais ref regroupée/filtrée
FICHIER_SORTIE = "stock_avec_nom_complet.xlsx"

# Colonnes que ni filtre_stock.py ni create_name.py ne modifient jamais :
# elles servent de clé de correspondance fiable entre les deux fichiers,
# à la place de "ref" (transformée par filtre_stock.py).
COLONNES_CLE = ["ref_fabricant", "qte", "emplacement", "libele"]


def normaliser(valeur):
    """
    Normalise une valeur pour la comparaison :
    - NaN -> chaîne vide
    - float entier (ex: 5.0) -> "5" au lieu de "5.0", pour éviter les
      faux négatifs si un fichier relit la quantité en float et l'autre
      en int
    - tout le reste -> texte, débarrassé des espaces en trop
    """

    if pd.isna(valeur):
        return ""

    if isinstance(valeur, float) and valeur.is_integer():
        valeur = int(valeur)

    return str(valeur).strip()


def construire_cle(ligne, colonnes=COLONNES_CLE):

    return tuple(
        normaliser(ligne[colonne])
        for colonne in colonnes
    )


def fusionner():

    stock = pd.read_excel(FICHIER_STOCK_ORIGINAL)
    stock_nomme = pd.read_excel(FICHIER_STOCK_NOMME)

    print(f"{FICHIER_STOCK_ORIGINAL} : {len(stock)} lignes")
    print(f"{FICHIER_STOCK_NOMME} : {len(stock_nomme)} lignes")

    for colonne in COLONNES_CLE:

        if colonne not in stock.columns:
            raise Exception(
                f"Colonne manquante dans {FICHIER_STOCK_ORIGINAL} : '{colonne}'"
            )

        if colonne not in stock_nomme.columns:
            raise Exception(
                f"Colonne manquante dans {FICHIER_STOCK_NOMME} : '{colonne}'"
            )

    if "nom_complet" not in stock_nomme.columns:
        raise Exception(
            f"La colonne 'nom_complet' est absente de {FICHIER_STOCK_NOMME}"
        )

    # 1) Construire le dictionnaire clé -> nom_complet à partir du
    #    fichier named_stock.xlsx.
    correspondance = {}
    cles_ambigues = 0

    for _, ligne in stock_nomme.iterrows():

        cle = construire_cle(ligne)
        nom = ligne["nom_complet"]

        if cle in correspondance and correspondance[cle] != nom:
            cles_ambigues += 1

        correspondance[cle] = nom

    if cles_ambigues:
        print(
            f"\n⚠️  {cles_ambigues} clé(s) associée(s) à plusieurs "
            "'nom_complet' différents dans named_stock.xlsx "
            "(seul le dernier rencontré a été conservé — à vérifier "
            "manuellement si ce nombre est élevé)."
        )

    # 2) Appliquer cette correspondance sur stock.xlsx, dont les 'ref'
    #    restent intactes et ne sont jamais utilisées pour la clé.
    noms_complets = []
    index_non_trouves = []

    for index, ligne in stock.iterrows():

        cle = construire_cle(ligne)
        nom = correspondance.get(cle)

        if nom is None:
            index_non_trouves.append(index)
            nom = ""

        noms_complets.append(nom)

    stock["nom_complet"] = noms_complets

    nb_trouves = len(stock) - len(index_non_trouves)

    print(f"\n✅ Lignes avec nom_complet trouvé : {nb_trouves}")
    print(f"❌ Lignes sans correspondance      : {len(index_non_trouves)}")

    if index_non_trouves:

        print(
            "\nExemples de lignes non appariées "
            "(à vérifier manuellement, ex: libellé/emplacement modifié "
            "entre-temps, ou ligne absente de named_stock.xlsx) :"
        )

        colonnes_affichees = ["ref"] + COLONNES_CLE

        print(
            stock.loc[
                index_non_trouves[:10],
                colonnes_affichees
            ].to_string()
        )

    stock.to_excel(FICHIER_SORTIE, index=False)

    print(f"\n📁 Fichier sauvegardé : {FICHIER_SORTIE}")


if __name__ == "__main__":
    fusionner()