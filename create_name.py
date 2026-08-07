import pandas as pd
import random
import requests
import json
import time

# Configuration
LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"
MODEL = "qwen3.5-4b"

INPUT_EXCEL = "stock_filtre.xlsx"
OUTPUT_EXCEL = "named_stock.xlsx"

COL_REF = "ref"
COL_LIBELE = "libele"
COL_NOM = "nom_complet"

# ------------------------------------------------------------------
# 1. Lecture
df = pd.read_excel(INPUT_EXCEL)
print(f"Fichier chargé : {len(df)} lignes")

if COL_NOM not in df.columns:
    df[COL_NOM] = ""

# ------------------------------------------------------------------
# 2. Fonctions d'appel LM Studio (identiques à votre script fonctionnel)
def appeler_llm(prompt):
    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": MODEL,
            "input": prompt,
            "temperature": 0,
            "reasoning": "off",
            "stream": False,
            "store": False,
            "max_output_tokens": 300
        },
        timeout=120
    )
    data = response.json()
    if "error" in data:
        raise Exception(data["error"]["message"])
    return data

def extraire_message(data):
    for item in data.get("output", []):
        if item.get("type") == "message":
            return item["content"]
    raise Exception("Aucun message retourné par LM Studio")

def ask_llm(prompt):
    try:
        data = appeler_llm(prompt)
        texte = extraire_message(data)
        return texte.strip()
    except Exception as e:
        print(f"  Erreur LLM : {e}")
        return None

# ------------------------------------------------------------------
# 3. Traitement par référence
groupes = df.groupby(COL_REF)

for ref, group in groupes:
    print(f"\nTraitement de la référence : {ref} ({len(group)} lignes)")

    libelles = group[COL_LIBELE].dropna().tolist()
    if not libelles:
        print("  Aucun libellé, on passe.")
        continue

    # Échantillonner jusqu'à 10 libellés (si un seul, il sera pris)
    if len(libelles) > 10:
        echantillon = random.sample(libelles, 10)
    else:
        echantillon = libelles

    # Construction du prompt adapté
    if len(echantillon) == 1:
        prompt = (
            f"Voici un libellé descriptif pour une référence technique :\n"
            f"- {echantillon[0]}\n"
            "Propose un nom unique et clair (en français, court) qui le résume. Ne donne que le nom, rien d'autre. Le nom ne devrait pas être technique et ne devrait pas être un diminutif ou bien de code ou de version. Pas de descriptif non plus"
        )
    else:
        prompt = (
            "Voici plusieurs libellés correspondant à une même référence technique :\n"
            + "\n".join(f"- {lib}" for lib in echantillon) +
            "\nPropose un nom unique et clair (en français, court) qui les résume. Ne donne que le nom, rien d'autre. Le nom ne devrait pas être technique et ne devrait pas être un diminutif ou bien de code ou de version. Pas de descriptif non plus"
        )

    # Appel LLM
    nom_propose = ask_llm(prompt)
    if nom_propose:
        df.loc[group.index, COL_NOM] = nom_propose
        print(f"  Nom proposé : {nom_propose}")
    else:
        print("  Échec, groupe non traité.")

    time.sleep(0.5)  # pause pour respecter l'API

# ------------------------------------------------------------------
# 4. Sauvegarde
df.to_excel(OUTPUT_EXCEL, index=False)
print(f"\n✅ Fichier sauvegardé : {OUTPUT_EXCEL}")