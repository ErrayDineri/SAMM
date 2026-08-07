import pandas as pd
from pathlib import Path

def extraire_uniques_tries(fichier_excel, nom_colonne='nom_complet', fichier_sortie='uniques_tries.txt'):
    """
    Extrait les valeurs uniques d'une colonne Excel, les trie et les sauvegarde dans un fichier texte.
    
    Args:
        fichier_excel (str): Chemin vers le fichier Excel
        nom_colonne (str): Nom de la colonne à traiter (par défaut: 'nom_complet')
        fichier_sortie (str): Nom du fichier de sortie (par défaut: 'uniques_tries.txt')
    """
    try:
        # Lire le fichier Excel
        df = pd.read_excel(fichier_excel)
        
        # Vérifier si la colonne existe
        if nom_colonne not in df.columns:
            print(f"Erreur : La colonne '{nom_colonne}' n'existe pas dans le fichier.")
            print(f"Colonnes disponibles : {', '.join(df.columns)}")
            return
        
        # Extraire les valeurs uniques (ignorer les NaN)
        valeurs_uniques = df[nom_colonne].dropna().unique()
        
        # Trier les valeurs
        valeurs_triees = sorted(valeurs_uniques)
        
        # Écrire dans le fichier texte
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            for valeur in valeurs_triees:
                f.write(f"{valeur}\n")
        
        print(f"✅ Extraction réussie !")
        print(f"📊 Nombre de valeurs uniques : {len(valeurs_triees)}")
        print(f"📁 Fichier sauvegardé : {fichier_sortie}")
        
        # Afficher les 10 premières valeurs
        print("\n📝 Aperçu des 10 premières valeurs :")
        for i, valeur in enumerate(valeurs_triees[:10], 1):
            print(f"{i:2d}. {valeur}")
            
    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier '{fichier_excel}' n'a pas été trouvé.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Remplacez 'votre_fichier.xlsx' par le chemin de votre fichier Excel
    fichier_excel = "named_stock.xlsx"  # À modifier
    
    # Appel de la fonction
    extraire_uniques_tries(fichier_excel, 'nom_complet', 'uniques_tries.txt')