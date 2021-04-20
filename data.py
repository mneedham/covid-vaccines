import streamlit as st
import pandas as pd
import numpy as np
from dateutil import parser
from utils import suffix, custom_strftime

# @st.cache 
def create_vaccines_dataframe(latest_date):
    dose1 = pd.read_csv(f"data/data_{latest_date.strftime('%Y-%b-%d')}-dose1.csv")
    dose2 = pd.read_csv(f"data/data_{latest_date.strftime('%Y-%b-%d')}-dose2.csv")
    df = pd.merge(dose1, dose2, on=["date", "areaName", "areaType", "areaCode"])

    df.loc[:, "totalByDay"] = df.newPeopleVaccinatedSecondDoseByPublishDate + df.newPeopleVaccinatedFirstDoseByPublishDate
    df.loc[:, "percentageFirstDose"] = 100.0* df.newPeopleVaccinatedFirstDoseByPublishDate / df.totalByDay

    cols = ["date", "newPeopleVaccinatedSecondDoseByPublishDate", "newPeopleVaccinatedFirstDoseByPublishDate", "totalByDay", "percentageFirstDose"]
    all_df = df[df.areaName == "United Kingdom"]
    all_df = all_df.loc[~pd.isna(all_df.totalByDay)]

    all_df = all_df.rename(columns={
        "newPeopleVaccinatedFirstDoseByPublishDate": "firstDose", 
        "newPeopleVaccinatedSecondDoseByPublishDate": "secondDose",
        "cumPeopleVaccinatedFirstDoseByPublishDate": "firstDoseCumulative",
        "cumPeopleVaccinatedSecondDoseByPublishDate": "secondDoseCumulative"
    })
    all_df.loc[:, "totalDoses"] = all_df.firstDose + all_df.secondDose
    return all_df

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

def all_vaccination_rates(spreadsheet):
    vaccinations = vaccinations_dataframe(spreadsheet)
    population = population_dataframe(spreadsheet)
    return compute_all_vaccination_rates(vaccinations, population)

def compute_all_vaccination_rates(vaccinations, population):    
    return (vaccinations.select_dtypes(exclude='string').div(population.select_dtypes(exclude='string')) * 100).combine_first(population)[vaccinations.columns]

def total_vaccination_rates(spreadsheet):
    vaccinations = vaccinations_dataframe(spreadsheet)
    population = population_dataframe(spreadsheet)
    return compute_total_vaccination_rates(vaccinations, population)

def compute_total_vaccination_rates(vaccinations, population):
    total = pd.DataFrame({"Vaccinations": vaccinations.sum(), "Population": population.sum()})
    total.loc[:, "Age"] = total.index
    total.loc[:, "%"] = total.Vaccinations / total.Population
    return total
