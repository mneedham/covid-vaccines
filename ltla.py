import streamlit as st
import pandas as pd
import numpy as np
from dateutil import parser
from utils import suffix, custom_strftime

st.set_page_config(layout="wide")

latest_date = parser.parse("2021-04-01")

spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_date.strftime('%-d-%B-%Y')}.xlsx"   

@st.cache 
def compute_vaccination_rates(spreadsheet):
    vaccinations = pd.read_excel(spreadsheet, "LTLA", usecols="B:M")
    columns = np.concatenate((vaccinations.loc[10,:][:4].values, vaccinations.loc[11,:][4:].values), axis=None)
    vaccinations = vaccinations.loc[14:327,]
    vaccinations.columns = columns
    vaccinations = vaccinations.drop(["Region Code (Administrative)", "Region Name (administrative)"], axis=1)
    vaccinations = vaccinations.convert_dtypes()

    population = pd.read_excel(spreadsheet, "Population estimates (NIMS)", usecols="B:L")
    population_columns = np.concatenate((population.loc[10,:][:2], population.loc[11, :][2:]), axis=None)

    population = population.loc[14:327,]
    population.columns = population_columns
    population.insert(loc=2, column="Under 50", value=population["Under 16"] + population["16-49"])
    population = population.drop(["Under 16", "16-49"], axis=1)
    population = population.convert_dtypes()

    return vaccinations.select_dtypes(exclude='string').div(population.select_dtypes(exclude='string')).combine_first(population)[vaccinations.columns]

combined = compute_vaccination_rates(spreadsheet)

st.title("Coronavirus Vaccines in the UK by Lower Tier Local Authority")
st.write(f"As of {custom_strftime('{S} %B %Y', latest_date)}")
st.markdown("This app contains charts showing how the Coronavirus vaccination program is going in the UK by Local Tier Local Authority, using the weekly data published at [england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations](https://www.england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations/)")

st.header("% of people vaccinated by age group")
st.dataframe(combined)

st.header("% of people vaccinated by local area")
option = st.selectbox('Select area:',
                       combined["LTLA Name"].values)

st.table(combined.loc[combined["LTLA Name"] == option].drop(["LTLA Name", "LTLA Code"], axis=1))
