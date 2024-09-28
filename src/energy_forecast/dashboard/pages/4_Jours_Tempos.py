"""Create the page for the prediction of Tempo days."""
import streamlit as st
import pandas as pd
from energy_forecast import ROOT_DIR
import locale

try :
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    logger.warning("Could not set locale to fr_FR.UTF-8")
    

gold_dir = ROOT_DIR / "data" / "gold"
tempo_prediction_file = gold_dir / "our_tempo_prediction.csv"

if __name__ == "__main__":

        
    st.title("Prévision des jours Tempo")
    today = pd.Timestamp.now().date()
    predictions = pd.read_csv(tempo_prediction_file, index_col=0, parse_dates=True)[today:]
    len_predictions = len(predictions)
    cols = st.columns(len_predictions)


    for offset, col in zip(range(len_predictions), cols):
        text = f"Prévision pour <p> {predictions.index[offset]:%a %d %B %Y}"
        type_day = predictions.iloc[offset]["our_tempo"]
        if type_day == "prediction_blanc":
            text += "\n\n <h1 style='color: black;'> Blanc </h1> \n\n"
            col.markdown(f"<div style='background-color: white ; padding: 10px ; border-radius: 10px ; color: black ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        elif type_day == "prediction_rouge":
            text += "\n\n <h1 style='color: white;'> Rouge </h1> \n\n"
            col.markdown(f"<div style='background-color: red ; padding: 10px ; border-radius: 10px ; color: white ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        elif type_day == "prediction_bleu":
            text += "\n\n <h1 style='color: white;'> Bleu </h1> \n\n"
            # an html blue square the size of the column with the text and H1 in white
            col.markdown(f"<div style='background-color: blue ; padding: 10px ; border-radius: 10px ; color: white ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        col.markdown("\n")

    for offset, col in zip(range(len_predictions), cols):
        text = f"Vrai couleur pour <p> {predictions.index[offset]:%a %d %B %Y}"
        type_day = predictions.iloc[offset]["Type_de_jour_TEMPO"]
        if type_day == "WHITE":
            text += "\n\n <h1 style='color: black;'> Blanc </h1> \n\n"
            col.markdown(f"<div style='background-color: white ; padding: 10px ; border-radius: 10px ; color: black ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        elif type_day == "RED":
            text += "\n\n <h1 style='color: white;'> Rouge </h1> \n\n"
            col.markdown(f"<div style='background-color: red ; padding: 10px ; border-radius: 10px ; color: white ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        elif type_day == "BLUE":
            text += "\n\n <h1 style='color: white;'> Bleu </h1> \n\n"
            # an html blue square the size of the column with the text and H1 in white
            col.markdown(f"<div style='background-color: blue ; padding: 10px ; border-radius: 10px ; color: white ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        else:
            text += "\n\n <h1 style='color: black;'> Inconnu </h1> \n\n"
            col.markdown(f"<div style='background-color: gray ; padding: 10px ; border-radius: 10px ; color: black ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        col.markdown("\n")
