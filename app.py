import streamlit as st

import SessionState as session_state

import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
from utils import suffix, custom_strftime
from ltla import compute_vaccination_rates, total_vaccination_rates

def daily(latest_daily_date, latest_weekly_date):
    all_df = create_vaccines_dataframe(latest_daily_date).copy()
    melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
    melted_df = melted_df[melted_df.areaName == "United Kingdom"]
    melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})    

    melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
    melted_df = melted_df[melted_df.areaName == "United Kingdom"]
    melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})

    melted_daily_doses = melted_df.loc[(melted_df["dose"] == "firstDose") | (melted_df["dose"] == "secondDose") | (melted_df["dose"] == "totalDoses")]
    melted_daily_doses = melted_daily_doses.loc[~pd.isna(melted_daily_doses.vaccinations)]
    melted_daily_doses = melted_daily_doses.sort_values(["date"])

    melted_daily_doses.loc[:, "dateWeek"] = pd.to_datetime(melted_daily_doses.date).dt.strftime('%Y-%U')
    melted_daily_doses.loc[melted_daily_doses.dose == "firstDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "firstDose"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[melted_daily_doses.dose == "secondDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "secondDose"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[:, "dayOfWeek"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%A"))
    melted_daily_doses.loc[:, "dayOfWeekIndex"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%w"))

    melted_first_second_daily_doses = melted_daily_doses.loc[(melted_daily_doses.dose.isin(["firstDose", "secondDose"]))]

    weekends = [value for value in melted_daily_doses.date.values if parser.parse(value).weekday() == 0]

    st.title("Daily Vaccines Administered")
    st.write(f"As of {custom_strftime('{S} %B %Y', latest_daily_date)}")
    st.write("This dashboard shows the total number of doses done at the end of each day. Data is only available from 11th January 2021")
    all_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(values=weekends)),
        tooltip=['sum(vaccinations)', 'date'],
        y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
        order=alt.Order('dose',sort='ascending'),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    ).properties( title='All doses by day', height=500)
    st.altair_chart(all_doses_chart, use_container_width=True)

    daily_left_column, daily_right_column = st.beta_columns(2)

    with daily_left_column:    
        rolling_average_chart = (alt.Chart(melted_daily_doses.loc[~pd.isna(melted_daily_doses.rollingAverage)], padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends)),
            tooltip=['rollingAverage', "date"],
            y=alt.Y('rollingAverage', axis=alt.Axis(title='Doses')),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
            )
        .properties(title="7-day rolling average", height=500))

        st.altair_chart(rolling_average_chart, use_container_width=True)

    with daily_right_column:
        percentage_doses_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends), scale=alt.Scale(padding=0)),
            tooltip=[alt.Tooltip('mean(percentageFirstDose)', title="% of first dose"), "date"],
            y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
            .properties(title="% of first doses by day", height=500))
        st.altair_chart(percentage_doses_chart, use_container_width=True)

def weekly(latest_daily_date, latest_weekly_date):
    all_df = create_vaccines_dataframe(latest_daily_date).copy()
    melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
    melted_df = melted_df[melted_df.areaName == "United Kingdom"]
    melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})    

    melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
    melted_df = melted_df[melted_df.areaName == "United Kingdom"]
    melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})

    melted_daily_doses = melted_df.loc[(melted_df["dose"] == "firstDose") | (melted_df["dose"] == "secondDose") | (melted_df["dose"] == "totalDoses")]
    melted_daily_doses = melted_daily_doses.loc[~pd.isna(melted_daily_doses.vaccinations)]
    melted_daily_doses = melted_daily_doses.sort_values(["date"])

    melted_daily_doses.loc[:, "dateWeek"] = pd.to_datetime(melted_daily_doses.date).dt.strftime('%Y-%U')
    melted_daily_doses.loc[melted_daily_doses.dose == "firstDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "firstDose"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[melted_daily_doses.dose == "secondDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "secondDose"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses"]["vaccinations"].rolling(7).mean()
    melted_daily_doses.loc[:, "dayOfWeek"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%A"))
    melted_daily_doses.loc[:, "dayOfWeekIndex"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%w"))

    melted_first_second_daily_doses = melted_daily_doses.loc[(melted_daily_doses.dose.isin(["firstDose", "secondDose"]))]

    weekends = [value for value in melted_daily_doses.date.values if parser.parse(value).weekday() == 0]

    st.title("Weekly Vaccines Administered")
    st.write(f"Using daily date as of {custom_strftime('{S} %B %Y', latest_daily_date)}")
    st.write("This dashboard shows the total number of doses done at the end of each week. Data is only available from 11th January 2021")
    weekly_left_column, weekly_right_column = st.beta_columns(2)
    with weekly_left_column: 
        all_doses_by_week_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            x=alt.X('dateWeek'),
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
            tooltip=['sum(vaccinations)'],
            order=alt.Order('dose',sort='ascending'),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        ).properties(title='All doses by week', height=500)
        st.altair_chart(all_doses_by_week_chart, use_container_width=True)

        all_df["dateWeek"] = pd.to_datetime(all_df.date).dt.strftime('%Y-%U')
        percentage_doses_by_week_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10})
            .mark_line(point=True)
            .encode(
                x=alt.X("dateWeek", scale=alt.Scale(padding=0)),
                tooltip=[alt.Tooltip('mean(percentageFirstDose)', title="% of first dose"), "dateWeek"],
                y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
            .properties(height=500,title="% of first doses by week"))

        st.altair_chart(percentage_doses_by_week_chart, use_container_width=True)

    with weekly_right_column:
        all_doses_by_week_chart2 = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X('dateWeek', scale=alt.Scale(padding=0)),
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
            tooltip=[alt.Tooltip('sum(vaccinations)', title="# of vaccinations"), 'dose', 'dateWeek'],
            # column='dateWeek',
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        ).properties(title='All doses by week', height=500)
        st.altair_chart(all_doses_by_week_chart2, use_container_width=True)

        weekday_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_area().encode(
            x=alt.X('dateWeek', scale=alt.Scale(padding=0)),
            tooltip=['sum(vaccinations)', 'dayOfWeek', 'date'],
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),  
            order=alt.Order('dayOfWeekIndex',sort='ascending'),          
            color=alt.Color('dayOfWeek', 
                legend=alt.Legend(orient='bottom', columns=4), 
                sort=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                scale=alt.Scale(
                    domain=[ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], 
                    range= ['#2E86C1', '#117864', '#76448A', '#F1C40F', '#E74C3C', '#FF69B4', '#00FFFF' ]
                )
            )
        ).properties( title='Doses by day of week', height=500)
        st.altair_chart(weekday_doses_chart, use_container_width=True)    

def overview(latest_daily_date, latest_weekly_date):    
    all_df = create_vaccines_dataframe(latest_daily_date)

    first_dose = all_df['firstDoseCumulative'].max()
    second_dose = all_df['secondDoseCumulative'].max()
    summary_df = pd.DataFrame({
        "Description": ["Population", "1st Dose", "2nd Dose"],
        "People": [f"{population:,}", f"{int(first_dose):,}", f"{int(second_dose):,}"],
        "Percentage": ["", f"{round(np.divide(first_dose, population) * 100, 2)}", f"{round(np.divide(second_dose, population) * 100, 2)}"]
    })
    summary_df.set_index('Description', inplace=True)

    st.title("All Vaccines Administered")

    st.header("Overview")
    st.write(f"Using daily data as of {custom_strftime('{S} %B %Y', latest_daily_date)}")
    st.table(summary_df) 

    melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
    melted_df = melted_df[melted_df.areaName == "United Kingdom"]
    melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})

    melted_cumulative_doses = melted_df.loc[(melted_df["dose"] == "firstDoseCumulative") | (melted_df["dose"] == "secondDoseCumulative"), :]
    melted_cumulative_doses.loc[:,"dateWeek"] = pd.to_datetime(melted_cumulative_doses.date).dt.strftime('%Y-%U')

    st.header("Cumulative Vaccines Administered")
    st.write(f"Using daily data as of {custom_strftime('{S} %B %Y', latest_daily_date)}")
    st.write("This chart shows the total number of doses done at the end of each week.")
    cumulative_first_doses_chart = alt.Chart(melted_cumulative_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
        x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending'), scale=alt.Scale(padding=0)),
        tooltip=['max(vaccinations)'],
        y=alt.Y('max(vaccinations)', axis=alt.Axis(title='Vaccinations')),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom')),
    ).properties(title='Cumulative doses', height=500)
    st.altair_chart(cumulative_first_doses_chart, use_container_width=True)

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    total = total_vaccination_rates(spreadsheet)
    total.loc[:, "%"] = (total.loc[:, "%"] * 100)
    total.loc[:, "Population"] = total["Population"].map('{:,d}'.format)
    total.loc[:, "Vaccinations"] = total["Vaccinations"].map('{:,d}'.format)

    st.header("By Age Group")
    st.write(f"Using weekly data as of {custom_strftime('{S} %B %Y', latest_weekly_date)}")
    st.table(total.drop(["Age"], axis=1))

    total_doses_chart = alt.Chart(total, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        y=alt.Y('Age', sort=["index"]),
        x=alt.X('%', scale=alt.Scale(domain=[0, 100])),    
        tooltip=["Age", alt.Tooltip('%', format='.2f')] 
    ).properties(title="Doses by age group")
    st.altair_chart(total_doses_chart, use_container_width=True)     

def ltla(latest_daily_date, latest_weekly_date):
    st.title("Vaccines Administered by Lower Tier Local Authority")
    st.write(f"Using weekly data as of {custom_strftime('{S} %B %Y', latest_weekly_date)}")
    st.markdown("This app contains charts showing how the Coronavirus vaccination program is going in the UK by Local Tier Local Authority, using the weekly data published at [england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations](https://www.england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations/)")
    
    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"

    st.header("All local areas")
    combined = compute_vaccination_rates(spreadsheet)
    formatting = {column: "{:.2f}" for column in set(combined.columns) - set(["LTLA Code", "LTLA Name"])}
    st.dataframe(combined.drop(["LTLA Code"], axis=1).style.format(formatting))

    st.header("Specific local area")
    option = st.multiselect('Select local area:', list(combined["LTLA Name"].values), ["Sutton", "Waverley"])

    if len(option) > 0:
        local_area = combined.loc[combined["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)
        melted_local_area = local_area.melt(value_vars=local_area.columns.drop(["LTLA Name"]), id_vars=["LTLA Name"])
        melted_local_area = melted_local_area.rename(columns={"value": "Percentage", "variable": "Age"})    
        melted_local_area.reset_index(level=0, inplace=True)
        weekday_doses_chart = alt.Chart(melted_local_area, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            y=alt.Y('LTLA Name', sort=["index"], axis=alt.Axis(labels=True, ticks=False), title=None),
            x=alt.X('Percentage', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('LTLA Name', legend=alt.Legend(orient='bottom', columns=2)),
            row=alt.Row("Age", title=None, sort=["index"]),        
            tooltip=["Age", alt.Tooltip('Percentage', format='.2f')] 
        ).properties(title="% of people vaccinated", width=350)
        st.altair_chart(weekday_doses_chart)  
    else:
        st.write("Select local areas to see the % of people vaccinated")

@st.cache 
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

PAGES = {
    "Overview": overview,
    "Daily Doses": daily,
    "Weekly Doses": weekly,
    "Local Authority": ltla
}

alt.themes.enable('fivethirtyeight')
st.set_page_config(layout="wide")
st.sidebar.title("UK Coronavirus Vaccines")

radio_list = list(PAGES.keys())
selection = st.sidebar.radio("Select Dashboard", radio_list)

page = PAGES[selection]

population = 68134973
latest_daily_date = parser.parse("2021-04-09")
latest_weekly_date = parser.parse("2021-04-08")
page(latest_daily_date, latest_weekly_date)