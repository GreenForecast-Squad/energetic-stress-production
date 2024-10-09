"""Landing page for the Energy Forecast dashboard."""
import streamlit as st
import streamlit as st
import pandas as pd
from energy_forecast import ROOT_DIR
import locale
import numpy as np
import logging
logger = logging.getLogger(__name__)
try :
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    logger.warning("Could not set locale to fr_FR.UTF-8")
    

gold_dir = ROOT_DIR / "data" / "gold"
tempo_prediction_file = gold_dir / "our_tempo_prediction.csv"

background_colors = {
    "Blanc": "white",
    "Rouge": "red",
    "Bleu": "blue",
    "Inconnu": "silver",
}
text_colors = {
    "Blanc": "black",
    "Rouge": "white",
    "Bleu": "white",
}

map_rte_signal_to_text = {
    "WHITE": "Blanc",
    "RED": "Rouge",
    "BLUE": "Bleu",
    np.nan: "Inconnu",
}
map_our_signal_to_text = {
    "prediction_blanc": "Blanc",
    "prediction_rouge": "Rouge",
    "prediction_bleu": "Bleu",
}

if __name__ == "__main__":
    st.set_page_config(
        page_title="Prévision ENR",
        page_icon="🌞",
    )
        
    st.title("🌞Calendier des jours Tempo❄️")
    st.markdown("Voici le calendrier des jours Tempo prédits par notre modèle et les jours Tempo réels selectionés par RTE.")
    today = pd.Timestamp.now().floor("D")
    predictions = pd.read_csv(tempo_prediction_file, index_col=0, parse_dates=True)[today:]
    predictions.index = pd.to_datetime(predictions.index, utc=True)
    len_predictions = len(predictions)
    cols = st.columns(len_predictions)

    # Create a table with two rows: one for our predictions and one for the true values
    st.write("### Tableau des prévisions et des valeurs réelles")

    # Create a DataFrame to hold the data for the table
    table_data = {
        "Date": predictions.index.strftime("%a %d %B %Y"),
        "Notre prévision": [map_our_signal_to_text[pred] for pred in predictions["our_tempo"]],
        "Valeur réelle": [map_rte_signal_to_text[true_val] for true_val in predictions["Type_de_jour_TEMPO"]],
    }

    table_df = pd.DataFrame(table_data).set_index("Date").T

    # Apply background colors to the table cells based on the content
    def apply_background_color(val):
        color = background_colors.get(val, "white")
        return f'background-color: {color}; color: {text_colors.get(val, "black")}'

    # Apply the background color function to the DataFrame
    styled_table_df = table_df.style.map(apply_background_color)

    # Display the styled table
    st.write(styled_table_df.to_html(), unsafe_allow_html=True)
    
    st.markdown("""## Comment ça marche?
Cette application est une démonstration d'une prévision énergétique simple.

Il est divisé en trois sections:

- <a href="Météo" target = "_self">Prévision météo</a> : analyse les prévision météo
- <a href="Production" target = "_self">Prévision de production électrique</a>: utilise la prévision météo pour estimer la production éolienne et solaire
- <a href="Consommation" target = "_self">Prévision de consommation</a>: récupère les données de consommation prévue par RTE
- Une fois la prévision de production et de consommation obtenue, la <a href="#2b45dae7" target = "_self">prévision Tempo</a> est calculée.
"""
    , unsafe_allow_html=True)
    
    # add section with a form so that the user can subscribe to newletter
    st.markdown("""## Souscrire à notre newsletter
Ce projet est encore en déveloopement et nous ajoutons de nouvelles fonctionnalités régulièrement.

Vous voulez être informé des nouvelles fonctionnalités de cette application?
Remplissez le formulaire ci-dessous pour vous inscrire à notre newsletter.""")
    with st.form(key="newsletter"):
        email = st.text_input("Votre adresse email")
        rgpd = st.checkbox("J'accepte que mes données soient utilisées pour m'envoyer des emails d'information (promis, pas de spams). "
                           "Aucune donnée ne sera partagée avec des tiers. "
                           "Vous pouvez vous désinscrire à tout moment. "
                           "Aucune publicité ne vous sera envoyée (parce que personne n'aime ça). "
                           "Les données seront stockées de manière sécurisée (si bien qu'il est problable qu'on en perde nous même l'accès). ")
        st.form_submit_button("Souscrire")
    
    # Store the email in the database
    if rgpd and email:
        from energy_forecast.dashboard.emails import store_email
        store_email(email)
        st.success(f"Merci pour votre inscription à notre newsletter.")
    elif rgpd and not email:
        st.error("Veuillez renseigner votre adresse email.")
    elif email and not rgpd:
        st.error("Vous devez accepter les conditions pour vous inscrire à la newsletter.")
    
    st.markdown("""## Contact
Pour toute question ou suggestion, n'hésitez pas à nous contacter à l'adresse suivante: contact@antoinetavant.fr""")

