"""Create the page for the prediction of Tempo days."""
import streamlit as st
import pandas as pd

if __name__ == "__main__":

    st.title("Prévision des jours Tempo")

    col1, col2, col3 = st.columns(3)

    today = pd.Timestamp.now().date()

    for offset, col in zip(range(3), [col1, col2, col3]):
        text = f"Prévision pour le {today + pd.Timedelta(days=offset)}"
        text += "\n\n <h1 style='color: white;'> Jour Bleu </h1> \n\n"
        # an html blue square the size of the column with the text and H1 in white
        col.markdown(f"<div style='background-color: blue ; padding: 10px ; border-radius: 10px ; color: white ; text-align: center'>{text}</div> \n", unsafe_allow_html=True)
        col.markdown("\n")