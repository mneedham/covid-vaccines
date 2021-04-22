import data as dt
import streamlit as st

@st.cache 
def create_vaccines_dataframe(latest_date):
    return dt.create_vaccines_dataframe(latest_date)

@st.cache
def vaccinations_dataframe(spreadsheet):
    return dt.vaccinations_dataframe(spreadsheet)

@st.cache
def population_dataframe(spreadsheet):
    return dt.population_dataframe(spreadsheet)
