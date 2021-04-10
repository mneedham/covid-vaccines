import streamlit as st
import pandas as pd
import numpy as np
from dateutil import parser
from utils import suffix, custom_strftime

from data import compute_vaccination_rates

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
