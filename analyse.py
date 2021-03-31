import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

population = 68134973
alt.themes.enable('fivethirtyeight')

latest_date = parser.parse("2021-03-31")

dose1 = pd.read_csv(f"data/data_{latest_date.strftime('%Y-%b-%d')}-dose1.csv")
dose2 = pd.read_csv(f"data/data_{latest_date.strftime('%Y-%b-%d')}-dose2.csv")
df = pd.merge(dose1, dose2, on=["date", "areaName", "areaType", "areaCode"])

df.loc[:, "totalByDay"] = df.newPeopleVaccinatedSecondDoseByPublishDate + df.newPeopleVaccinatedFirstDoseByPublishDate
df.loc[:, "percentageFirstDose"] = 100.0* df.newPeopleVaccinatedFirstDoseByPublishDate / df.totalByDay

cols = ["date", "newPeopleVaccinatedSecondDoseByPublishDate", "newPeopleVaccinatedFirstDoseByPublishDate", "totalByDay", "percentageFirstDose"]
all_df = df[df.areaName == "United Kingdom"]

first_dose = all_df['cumPeopleVaccinatedFirstDoseByPublishDate'].max()
second_dose = all_df['cumPeopleVaccinatedSecondDoseByPublishDate'].max()

all_df = all_df.rename(columns={
    "newPeopleVaccinatedFirstDoseByPublishDate": "firstDose", 
    "newPeopleVaccinatedSecondDoseByPublishDate": "secondDose",
    "cumPeopleVaccinatedFirstDoseByPublishDate": "firstDoseCumulative",
    "cumPeopleVaccinatedSecondDoseByPublishDate": "secondDoseCumulative"
})
all_df.loc[:, "totalDoses"] = all_df.firstDose + all_df.secondDose

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

melted_first_second_daily_doses = melted_daily_doses.loc[(melted_daily_doses.dose.isin(["firstDose", "secondDose"]))]

melted_cumulative_doses = melted_df.loc[(melted_df["dose"] == "firstDoseCumulative") | (melted_df["dose"] == "secondDoseCumulative"), :]
melted_cumulative_doses.loc[:,"dateWeek"] = pd.to_datetime(melted_cumulative_doses.date).dt.strftime('%Y-%U')

summary_df = pd.DataFrame({
    "Description": ["Population", "1st Dose", "2nd Dose"],
    "Value": [f"{population:,}", f"{int(first_dose):,}", f"{int(second_dose):,}"],
    "Percentage": ["", f"{round(np.divide(first_dose, population) * 100, 2)}", f"{round(np.divide(second_dose, population) * 100, 2)}"]
})
summary_df.set_index('Description', inplace=True)

st.set_page_config(layout="wide")
st.title("Coronavirus Vaccines in the UK")
st.write(f"As of {custom_strftime('{S} %B %Y', latest_date)}")
st.write("This app contains charts showing how the Coronavirus vaccination program is going in the UK. It's based on data from https://coronavirus.data.gov.uk/")
st.header("Overview")
st.table(summary_df)

st.header("Cumulative Vaccine Doses")
st.write("This chart shows the total number of doses done at the end of each week.")

cumulative_first_doses_chart = alt.Chart(melted_cumulative_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
    # x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending', format=("%b %d"))),
    x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending')),
    tooltip=['max(vaccinations)'],
    y=alt.Y('max(vaccinations)', axis=alt.Axis(title='Vaccinations')),
    color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
).properties(title='Cumulative doses', height=500)
st.altair_chart(cumulative_first_doses_chart, use_container_width=True)

dose1.loc[:, "dateWeek"] = pd.to_datetime(dose1.date).dt.strftime('%Y-%U')
# dose1_dates = pd.to_datetime(dose1.date)
# dose1["dateWeek"] = dose1_dates.apply(lambda dt: (dt - timedelta(days=dt.weekday()) + timedelta(days=6)))
dose1.loc[:, "doses"] = dose1["newPeopleVaccinatedFirstDoseByPublishDate"]
dose1.loc[:, "cumulativeDoses"] = dose1["cumPeopleVaccinatedFirstDoseByPublishDate"]


dose2.loc[:, "dateWeek"] = pd.to_datetime(dose2.date).dt.strftime('%Y-%U')
# dose2_dates = pd.to_datetime(dose2.date)
# dose2["dateWeek"] = dose2_dates.apply(lambda dt: dt - timedelta(days=dt.weekday()) + timedelta(days=6))
dose2.loc[:, "doses"] = dose2["newPeopleVaccinatedSecondDoseByPublishDate"]
dose2.loc[:, "cumulativeDoses"] = dose2["cumPeopleVaccinatedSecondDoseByPublishDate"]

st.header("Daily Vaccine Doses")
st.write("Daily figures are only available from 11th January 2021")

daily_left_column, daily_right_column = st.beta_columns(2)
weekends = [value for value in melted_daily_doses.date.values if parser.parse(value).weekday() == 0]

with daily_left_column:    
    all_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        x=alt.X('date', axis=alt.Axis(values=weekends)),
        tooltip=['sum(vaccinations)', 'date'],
        y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
        order=alt.Order('dose',sort='ascending'),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    ).properties( title='All doses by day', height=500)
    st.altair_chart(all_doses_chart, use_container_width=True)

    rolling_average_chart = (alt.Chart(melted_daily_doses.loc[~pd.isna(melted_daily_doses.rollingAverage)], padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
        x=alt.X("date", axis=alt.Axis(values=weekends)),
        tooltip=['rollingAverage'],
        y=alt.Y('rollingAverage', axis=alt.Axis(title='Doses')),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        )
    .properties(title="7-day rolling average", height=500))

    st.altair_chart(rolling_average_chart, use_container_width=True)

with daily_right_column:
    weekday_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        x=alt.X('dayOfWeek', sort=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
        tooltip=['mean(vaccinations)', 'dayOfWeek'],
        y=alt.Y('mean(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
        order=alt.Order('dose',sort='ascending'),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    ).properties( title='Average doses by day of week', height=500)
    st.altair_chart(weekday_doses_chart, use_container_width=True)    

    percentage_doses_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
        x=alt.X("date", axis=alt.Axis(values=weekends)),
        tooltip=['mean(percentageFirstDose)'],
        y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
        .properties(title="% of first doses by day", height=500))

    st.altair_chart(percentage_doses_chart, use_container_width=True)


st.header("Weekly Vaccine Doses")
st.write("These charts show the number of vaccine doses given, grouped by week number.")

weekly_left_column, weekly_right_column = st.beta_columns(2)

with weekly_left_column: 
    all_doses_by_week_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        x='dateWeek',
        y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
        tooltip=['sum(vaccinations)'],
        order=alt.Order('dose',sort='ascending'),
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    ).properties(title='All doses by week', height=500)
    st.altair_chart(all_doses_by_week_chart, use_container_width=True)

with weekly_right_column:
    all_doses_by_week_chart2 = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
        x=alt.X('dose', axis=alt.Axis(labels=False, ticks=False), title=None),
        y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
        tooltip=['sum(vaccinations)'],
        column='dateWeek',
        color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    ).properties(title='All doses by week')
    st.altair_chart(all_doses_by_week_chart2)

all_df["dateWeek"] = pd.to_datetime(all_df.date).dt.strftime('%Y-%U')
percentage_doses_by_week_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10})
    .mark_line(point=True)
    .encode(
        x="dateWeek",
        tooltip=['mean(percentageFirstDose)'],
        y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
    .properties(height=500,title="% of first doses by week"))

st.altair_chart(percentage_doses_by_week_chart, use_container_width=True)

