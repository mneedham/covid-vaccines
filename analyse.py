import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser

population = 68134973
alt.themes.enable('fivethirtyeight')

dose1 = pd.read_csv("data_2021-Mar-26-dose1.csv")
dose2 = pd.read_csv("data_2021-Mar-26-dose2.csv")
df = pd.merge(dose1, dose2, on=["date", "areaName", "areaType", "areaCode"])

df["totalByDay"] = df.newPeopleVaccinatedSecondDoseByPublishDate + df.newPeopleVaccinatedFirstDoseByPublishDate
df["percentageFirstDose"] = 100.0* df.newPeopleVaccinatedFirstDoseByPublishDate / df.totalByDay

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
melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative"], id_vars=["date", "areaName"])
melted_df = melted_df[melted_df.areaName == "United Kingdom"]
melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})

melted_daily_doses = melted_df.loc[(melted_df["dose"] == "firstDose") | (melted_df["dose"] == "secondDose")]
melted_daily_doses = melted_daily_doses[~pd.isna(melted_daily_doses.vaccinations)]
melted_daily_doses = melted_daily_doses.sort_values(["date"])

melted_daily_doses.loc[:, "dateWeek"] = pd.to_datetime(melted_daily_doses.date).dt.strftime('%Y-%U')
melted_daily_doses.loc[melted_daily_doses.dose == "firstDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "firstDose"]["vaccinations"].rolling(7).mean()
melted_daily_doses.loc[melted_daily_doses.dose == "secondDose", "rollingAverage"] = melted_daily_doses.loc[melted_daily_doses.dose == "secondDose"]["vaccinations"].rolling(7).mean()

melted_cumulative_doses = melted_df.loc[(melted_df["dose"] == "firstDoseCumulative") | (melted_df["dose"] == "secondDoseCumulative")]
melted_cumulative_doses["dateWeek"] = pd.to_datetime(melted_cumulative_doses.date).dt.strftime('%Y-%U')

summary_df = pd.DataFrame({
    "Description": ["Population", "1st Dose", "2nd Dose"],
    "Value": [f"{population:,}", f"{int(first_dose):,}", f"{int(second_dose):,}"],
    "Percentage": ["", f"{round(np.divide(first_dose, population) * 100, 2)}", f"{round(np.divide(second_dose, population) * 100, 2)}"]
})
summary_df.set_index('Description', inplace=True)

st.header("Coronavirus Vaccines in the UK")
st.table(summary_df)

st.subheader("Cumulative Vaccine Doses")

cumulative_first_doses_chart = alt.Chart(melted_cumulative_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
    # x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending', format=("%b %d"))),
    x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending')),
    tooltip=['max(vaccinations)'],
    y=alt.Y('max(vaccinations)', axis=alt.Axis(title='Vaccinations')),
    color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
).properties(width=800,height=400, title='Cumulative doses')
st.altair_chart(cumulative_first_doses_chart)

dose1["dateWeek"] = pd.to_datetime(dose1.date).dt.strftime('%Y-%U')
# dose1_dates = pd.to_datetime(dose1.date)
# dose1["dateWeek"] = dose1_dates.apply(lambda dt: (dt - timedelta(days=dt.weekday()) + timedelta(days=6)))
dose1["doses"] = dose1["newPeopleVaccinatedFirstDoseByPublishDate"]
dose1["cumulativeDoses"] = dose1["cumPeopleVaccinatedFirstDoseByPublishDate"]


dose2["dateWeek"] = pd.to_datetime(dose2.date).dt.strftime('%Y-%U')
# dose2_dates = pd.to_datetime(dose2.date)
# dose2["dateWeek"] = dose2_dates.apply(lambda dt: dt - timedelta(days=dt.weekday()) + timedelta(days=6))
dose2["doses"] = dose2["newPeopleVaccinatedSecondDoseByPublishDate"]
dose2["cumulativeDoses"] = dose2["cumPeopleVaccinatedSecondDoseByPublishDate"]

st.subheader("Daily Vaccine Doses")

st.write("Daily figures are only available from 11th January 2021")

weekends = [value for value in melted_daily_doses.date.values if parser.parse(value).weekday() == 0]
all_doses_chart = alt.Chart(melted_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
    x=alt.X('date', axis=alt.Axis(values=weekends)),
    tooltip=['sum(vaccinations)', 'date'],
    y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
    color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
).properties(width=800,height=400, title='All doses by day')
st.altair_chart(all_doses_chart)

percentage_doses_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
    x=alt.X("date", axis=alt.Axis(values=weekends)),
    tooltip=['mean(percentageFirstDose)'],
    y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
    .properties(width=800,height=300,title="% of first doses by day"))

st.altair_chart(percentage_doses_chart)

rolling_average_chart = (alt.Chart(melted_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
    x=alt.X("date", axis=alt.Axis(values=weekends)),
    tooltip=['rollingAverage'],
    y=alt.Y('rollingAverage', axis=alt.Axis(title='Doses')),
    color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
    )
.properties(width=800,height=400,title="Rolling average of doses"))

st.altair_chart(rolling_average_chart)


all_doses_by_week_chart = alt.Chart(melted_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar(size=50).encode(
    x='dateWeek',
    y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
    tooltip=['sum(vaccinations)'],
    color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
).properties(width=800,height=400, title='All doses by week')
st.altair_chart(all_doses_by_week_chart)

all_doses_by_week_chart2 = alt.Chart(melted_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
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
    .properties(width=800,height=300,title="% of first doses by week"))

st.altair_chart(percentage_doses_by_week_chart)
