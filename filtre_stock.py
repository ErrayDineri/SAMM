import pandas as pd
import re

def extract_base(value):
    """
    Extrait la partie avant le premier chiffre,
    en conservant lettres, espaces, underscores et tirets.
    Exemple : 'FORET CARBURE 1,9x' -> 'FORET CARBURE'
    """
    if isinstance(value, str):
        match = re.match(r'^([A-Za-z _-]+)', value)
        if match:
            return match.group(1).strip()   # supprime les espaces en trop
        else:
            return value.strip()            # cas sans chiffres
    return value

# ------------------------------------------------------------
# 1. Lecture du fichier Excel
# ------------------------------------------------------------
file_path = "stock.xlsx"          # nom du fichier source
df = pd.read_excel(file_path, header=0)   # la première ligne est l'en-tête

# ------------------------------------------------------------
# 2. Application du filtrage sur la colonne 'ref'
# ------------------------------------------------------------
df['ref'] = df['ref'].apply(extract_base)

# ------------------------------------------------------------
# 3. (Optionnel) Tri par la nouvelle colonne 'ref'
# ------------------------------------------------------------
df = df.sort_values(by='ref').reset_index(drop=True)

# ------------------------------------------------------------
# 4. Sauvegarde dans un nouveau fichier (ou écraser)
# ------------------------------------------------------------
output_path = "stock_filtre.xlsx"
df.to_excel(output_path, index=False)

print(f"✅ Opération terminée. Fichier sauvegardé sous : {output_path}")
print(f"   {len(df)} lignes conservées.")
print("   Exemple des premières références :")
print(df['ref'].head(10).to_list())