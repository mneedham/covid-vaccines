import streamlit as st
import pandas as pd
import numpy as np
from dateutil import parser
from utils import suffix, custom_strftime

@st.cache
def vaccinations_dataframe(spreadsheet):
    vaccinations = pd.read_excel(spreadsheet, "LTLA", usecols="B:M")
    columns = np.concatenate((vaccinations.loc[10,:][:4].values, vaccinations.loc[11,:][4:].values), axis=None)
    vaccinations = vaccinations.loc[14:327,]
    vaccinations.columns = columns
    vaccinations = vaccinations.drop(["Region Code (Administrative)", "Region Name (administrative)"], axis=1)
    vaccinations = vaccinations.convert_dtypes()
    return vaccinations    

@st.cache
def population_dataframe(spreadsheet):
    population = pd.read_excel(spreadsheet, "Population estimates (NIMS)", usecols="B:L")
    population_columns = np.concatenate((population.loc[10,:][:2], population.loc[11, :][2:]), axis=None)
    population = population.loc[14:327,]
    population.columns = population_columns
    population.insert(loc=2, column="Under 50", value=population["Under 16"] + population["16-49"])
    population = population.drop(["Under 16", "16-49"], axis=1)
    population = population.convert_dtypes()
    return population

def compute_vaccination_rates(spreadsheet):
    vaccinations = vaccinations_dataframe(spreadsheet)
    population = population_dataframe(spreadsheet)
    return (vaccinations.select_dtypes(exclude='string').div(population.select_dtypes(exclude='string')) * 100).combine_first(population)[vaccinations.columns]

def total_vaccination_rates(spreadsheet):
    vaccinations = vaccinations_dataframe(spreadsheet)
    population = population_dataframe(spreadsheet)
    total = pd.DataFrame({"Vaccinations": vaccinations.sum(), "Population": population.sum()})
    total.loc[:, "Age"] = total.index
    total.loc[:, "%"] = total.Vaccinations / total.Population
    return total

def main():
    st.set_page_config(layout="wide")

    latest_date = parser.parse("2021-04-01")
    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_date.strftime('%-d-%B-%Y')}.xlsx"

    combined = compute_vaccination_rates(spreadsheet)

    st.title("Coronavirus Vaccines in the UK by Lower Tier Local Authority")
    st.write(f"As of {custom_strftime('{S} %B %Y', latest_date)}")
    st.markdown("This app contains charts showing how the Coronavirus vaccination program is going in the UK by Local Tier Local Authority, using the weekly data published at [england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations](https://www.england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations/)")

    st.header("% of people vaccinated by age group")
    st.dataframe(combined.drop(["LTLA Code"], axis=1))

    st.header("% of people vaccinated by local area")
    option = st.selectbox('Select local area:', combined["LTLA Name"].values)

    st.table(combined.loc[combined["LTLA Name"] == option].drop(["LTLA Name", "LTLA Code"], axis=1))

if __name__ == "__main__":
    main()
