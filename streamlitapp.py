import streamlit as st
import json
import textwrap

from llm import analyser_besoin
from stock import Stock
from kits import charger_kits, rechercher_kit, ajouter_kit


# -------------------------
# Configuration
# -------------------------

st.set_page_config(
    page_title="SAMM",
    page_icon="⚡",
    layout="wide"
)


# -------------------------
# CSS
# -------------------------

st.markdown(
    """
    <style>

    :root {
        --samm-primary: #1565C0;
        --samm-primary-light: #E8F1FB;
        --samm-border: #E3E7ED;
        --samm-text: #212121;
        --samm-muted: #6B7280;
    }

    /* Fond général un peu plus doux que le blanc pur */
    .stApp {
        background: #F7F9FC;
    }

    /* -------- Header -------- */
    h1 {
        font-weight: 700 !important;
        color: var(--samm-text) !important;
    }

    /* -------- Barre de recherche -------- */
    .stTextInput input {
        border-radius: 10px !important;
        border: 1px solid var(--samm-border) !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
    }
    .stTextInput input:focus {
        border-color: var(--samm-primary) !important;
        box-shadow: 0 0 0 2px var(--samm-primary-light) !important;
    }

    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        transition: transform 0.08s ease, box-shadow 0.15s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(21,101,192,0.18);
    }

    /* -------- Carte composant -------- */
    /* Hauteur libre (min-height au lieu de height fixe) + flexbox
       pour que le contenu s'adapte proprement, quelle que soit la
       longueur du nom du composant. */
    .piece-card {
        border: 1px solid var(--samm-border);
        border-radius: 16px;
        padding: 20px 20px 16px 20px;
        background: #FFFFFF;
        min-height: 168px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0px 2px 8px rgba(16,24,40,0.06);
        margin-bottom: 12px;
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
    }

    .piece-card:hover {
        border-color: var(--samm-primary);
        box-shadow: 0px 6px 16px rgba(21,101,192,0.12);
    }

    /* Carte actuellement affichée dans le détail : mise en évidence */
    .piece-card.selected {
        border: 1.5px solid var(--samm-primary);
        background: var(--samm-primary-light);
    }

    .piece-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }

    .piece-icon {
        font-size: 18px;
        line-height: 1;
    }

    /* Titre sur 2 lignes max, avec troncature propre au lieu
       de déborder de la carte */
    .piece-title {
        font-size: 15.5px;
        font-weight: 600;
        color: var(--samm-text);
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-transform: capitalize;
    }

    .piece-count-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
    }

    .piece-count {
        font-size: 30px;
        font-weight: 700;
        color: var(--samm-primary);
        line-height: 1;
    }

    .piece-count.zero {
        color: #B0B7C3;
    }

    .piece-subtitle {
        color: var(--samm-muted);
        font-size: 12.5px;
    }

    /* Rapproche le bouton "Voir" de sa carte au-dessus */
    div[data-testid="column"] .stButton {
        margin-top: -6px;
    }

    /* -------- Tableau de détails -------- */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid var(--samm-border) !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)



# -------------------------
# Chargement stock
# -------------------------

@st.cache_resource
def charger_stock():

    return Stock(
        "stock.xlsx"
    )


stock = charger_stock()



# -------------------------
# Session
# -------------------------

if "pieces" not in st.session_state:
    st.session_state.pieces = []


if "resultats" not in st.session_state:
    st.session_state.resultats = {}


if "selection" not in st.session_state:
    st.session_state.selection = None


if "source_pieces" not in st.session_state:
    st.session_state.source_pieces = None


if "kit_utilise" not in st.session_state:
    st.session_state.kit_utilise = None


if "derniere_question" not in st.session_state:
    st.session_state.derniere_question = ""



# -------------------------
# Header
# -------------------------

st.title("⚡ SAMM")

st.caption(
    "Assistant intelligent de recherche de composants industriels"
)



# -------------------------
# Recherche
# -------------------------

# st.form permet de déclencher la recherche aussi bien avec la
# touche "Entrée" dans le champ qu'en cliquant sur le bouton.
with st.form(key="recherche_form"):

    question = st.text_input(
        "Besoin",
        placeholder=
        "Ex : créer un départ moteur triphasé"
    )

    lancer_recherche = st.form_submit_button(
        "🔎 Analyser",
        type="primary"
    )


if lancer_recherche:

    if not question.strip():

        st.warning(
            "Veuillez saisir un besoin"
        )

    else:

        with st.spinner(
            "Analyse du besoin..."
        ):

            # 1) On cherche d'abord si un kit connu correspond déjà
            #    à ce besoin (recherche floue sur le nom/alias du kit).
            #    Si oui : résultat instantané, sans appel au LLM.
            kits_disponibles = charger_kits()

            kit_trouve = rechercher_kit(
                question,
                kits_disponibles
            )

            if kit_trouve:

                pieces = kit_trouve["pieces"]

                st.session_state.source_pieces = "kit"
                st.session_state.kit_utilise = kit_trouve["nom"]

            else:

                # 2) Aucun kit ne correspond : on retombe sur
                #    l'analyse par l'IA, comme avant.
                pieces = analyser_besoin(
                    question
                )

                st.session_state.source_pieces = "ia"
                st.session_state.kit_utilise = None


            st.session_state.pieces = pieces
            st.session_state.derniere_question = question


            resultats = {}


            for piece in pieces:

                resultats[piece] = (
                    stock.rechercher(
                        piece
                    )
                )


            st.session_state.resultats = resultats

            st.session_state.selection = None



# -------------------------
# Indicateur de source (kit connu vs analyse IA)
# -------------------------

if st.session_state.pieces:

    if st.session_state.source_pieces == "kit":

        st.success(
            f"⚡ Kit reconnu : **{st.session_state.kit_utilise}** "
            "— résultat instantané, sans appel à l'IA."
        )

    elif st.session_state.source_pieces == "ia":

        st.info(
            "🤖 Besoin inédit : analysé par l'IA "
            "(aucun kit existant ne correspondait)."
        )

        with st.expander(
            "💾 Enregistrer ce besoin comme kit pour la prochaine fois"
        ):

            nom_kit = st.text_input(
                "Nom du kit",
                value=st.session_state.derniere_question.strip().capitalize(),
                key="nom_nouveau_kit"
            )

            if st.button(
                "Enregistrer le kit",
                key="enregistrer_kit"
            ):

                if nom_kit.strip():

                    ajouter_kit(
                        nom_kit.strip(),
                        st.session_state.pieces,
                        alias=[st.session_state.derniere_question.strip()]
                    )

                    st.success(
                        f"Kit « {nom_kit.strip()} » enregistré ! "
                        "Il sera reconnu instantanément la prochaine fois."
                    )

                else:

                    st.warning(
                        "Veuillez donner un nom au kit avant d'enregistrer."
                    )



# -------------------------
# Cartes composants
# -------------------------

if st.session_state.pieces:


    st.subheader(
        "Composants nécessaires"
    )


    # Nombre de colonnes adapté au nombre de pièces (max 4),
    # pour éviter des cartes étirées quand il y en a peu.
    nb_colonnes = min(4, len(st.session_state.pieces)) or 1

    cols = st.columns(nb_colonnes)


    for index, piece in enumerate(
        st.session_state.pieces
    ):


        with cols[index % nb_colonnes]:


            nombre = len(
                st.session_state.resultats
                .get(piece, [])
            )

            est_selection = (
                st.session_state.selection == piece
            )

            classe_carte = (
                "piece-card selected"
                if est_selection
                else "piece-card"
            )

            classe_count = (
                "piece-count zero"
                if nombre == 0
                else "piece-count"
            )


            carte_html = f"""
            <div class="{classe_carte}">
                <div>
                    <div class="piece-header">
                        <span class="piece-icon">🔩</span>
                        <span class="piece-title">{piece}</span>
                    </div>
                </div>
                <div>
                    <div class="piece-count-row">
                        <span class="{classe_count}">{nombre}</span>
                    </div>
                    <div class="piece-subtitle">
                        référence{"s" if nombre != 1 else ""} disponible{"s" if nombre != 1 else ""}
                    </div>
                </div>
            </div>
            """

            # dedent() retire l'indentation commune : sans ça, Streamlit/Markdown
            # traite un bloc indenté de 4+ espaces comme du code et affiche
            # le HTML brut au lieu de le rendre.
            st.markdown(
                textwrap.dedent(carte_html).strip(),
                unsafe_allow_html=True
            )


            if st.button(
                "👁️ Voir" if not est_selection else "✓ Sélectionné",
                key=f"voir_{index}",
                type="primary" if est_selection else "secondary",
                use_container_width=True
            ):

                st.session_state.selection = piece
                st.rerun()



# -------------------------
# Détails
# -------------------------

if st.session_state.selection:


    piece = st.session_state.selection


    st.divider()


    st.subheader(
        f"📦 {piece}"
    )


    resultats = (
        st.session_state.resultats
        .get(piece, [])
    )


    if resultats:


        st.dataframe(
            resultats,
            hide_index=True,
            use_container_width=True
        )


        with st.expander(
            "Voir JSON"
        ):

            st.code(
                json.dumps(
                    resultats,
                    indent=2,
                    ensure_ascii=False
                ),
                language="json"
            )


    else:


        st.info(
            "Aucune référence trouvée"
        )