import streamlit as st

import SessionState as session_state

import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
from utils import suffix, custom_strftime, make_charts_responsive
import data as dt

def daily(latest_daily_date, latest_weekly_date):
    all_df = dt.create_vaccines_dataframe(latest_daily_date).copy()
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
    st.write("This dashboard shows the total number of doses done at the end of each day. Data is only available from 11th January 2021")

    left1, right1 = st.beta_columns(2)

    with left1:
        st.header("All doses by day")
        all_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            x=alt.X('date', axis=alt.Axis(values=weekends)),
            tooltip=[alt.Tooltip('sum(vaccinations)', format=","), 'date'],
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
            order=alt.Order('dose',sort='ascending'),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        ).properties( height=500)
        st.altair_chart(all_doses_chart, use_container_width=True)

    with right1:
        st.header("% of first doses by day")
        percentage_doses_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends), scale=alt.Scale(padding=0)),
            tooltip=[alt.Tooltip('mean(percentageFirstDose)', title="% of first dose", format=".2f"), "date"],
            y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
            .properties(height=500))
        st.altair_chart(percentage_doses_chart, use_container_width=True)        


    left2, right2 = st.beta_columns(2)

    with left2:    
        st.header("7-day rolling average")
        rolling_average_chart = (alt.Chart(melted_daily_doses.loc[~pd.isna(melted_daily_doses.rollingAverage)], padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends)),
            tooltip=[alt.Tooltip('rollingAverage', format=",.0f"), "date"],
            y=alt.Y('rollingAverage', axis=alt.Axis(title='Doses')),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
            )
        .properties(height=500))

        st.altair_chart(rolling_average_chart, use_container_width=True)

    with right2:
        st.header("Trend by day of week")
        all_df.loc[:, "dayOfWeek"] = all_df["date"].apply(lambda date: parser.parse(date).strftime("%A"))
        all_df.loc[:, "dayOfWeekIndex"] = all_df["date"].apply(lambda date: parser.parse(date).strftime("%w"))
        by_day_of_week = all_df[["date", "totalByDay", "dayOfWeek", "dayOfWeekIndex"]]
        day_of_week_grouping = by_day_of_week.sort_values("date").groupby(["dayOfWeek", "dayOfWeekIndex"])
        this_week = day_of_week_grouping.nth(-1)[["totalByDay"]]
        last_week = day_of_week_grouping.nth(-2)[["totalByDay"]]
        
        indices = list(this_week.index) 

        latest = pd.merge(last_week, this_week, on=["dayOfWeek", "dayOfWeekIndex"], suffixes=["LastWeek", "ThisWeek"])        
        # latest.loc[:, "dayOfWeek"] = [index[0] for index in indices]
        latest = latest.reset_index(drop=True)

        latest.loc[:, "Day"] = [index[0] for index in indices]        
        latest.loc[:, "dayOfWeekIndex"] = [index[1] for index in indices]        
        latest.loc[:, "totalByDayLastWeek"] = latest.totalByDayLastWeek.astype(int)
        latest.loc[:, "totalByDayThisWeek"] = latest.totalByDayThisWeek.astype(int)
        latest.loc[:, "Change"] = 100 * (latest.totalByDayThisWeek - latest.totalByDayLastWeek) / latest.totalByDayLastWeek

        latest = latest.rename(columns = {"totalByDayLastWeek": "Previous Week", "totalByDayThisWeek": "Latest Week"})
        sorted_latest = latest.sort_values("dayOfWeekIndex").drop(["dayOfWeekIndex"], axis=1)

        st.table((sorted_latest[["Day", "Previous Week", "Latest Week", "Change"]].style
            .applymap(lambda val: 'background-color: yellow; font-weight: 700;' if val == (latest_daily_date- timedelta(days=1)).strftime("%A") else '')
            .format({
                "Previous Week": "{:,d}",
                "Latest Week": "{:,d}",
                "Change": "{:.2f}"
            })
            .bar(align='mid', color=['red', 'lightgreen'], subset=["Change"]))
        )

def weekly(latest_daily_date, latest_weekly_date):
    all_df = dt.create_vaccines_dataframe(latest_daily_date).copy()
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
    st.write("This dashboard shows the total number of doses done at the end of each week. Data is only available from 11th January 2021")
    weekly_left_column, weekly_right_column = st.beta_columns(2)
    with weekly_left_column: 
        all_doses_by_week_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            x=alt.X('dateWeek'),
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
            tooltip=[alt.Tooltip('sum(vaccinations)', format=",")],
            order=alt.Order('dose',sort='ascending'),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        ).properties(title='All doses by week', height=500)
        st.altair_chart(all_doses_by_week_chart, use_container_width=True)

        all_df["dateWeek"] = pd.to_datetime(all_df.date).dt.strftime('%Y-%U')
        percentage_doses_by_week_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10})
            .mark_line(point=True)
            .encode(
                x=alt.X("dateWeek", scale=alt.Scale(padding=0)),
                tooltip=[alt.Tooltip('mean(percentageFirstDose)', title="% of first dose", format=".2f"), "dateWeek"],
                y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
            .properties(height=500,title="% of first doses by week"))

        st.altair_chart(percentage_doses_by_week_chart, use_container_width=True)

    with weekly_right_column:
        all_doses_by_week_chart2 = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X('dateWeek', scale=alt.Scale(padding=0)),
            y=alt.Y('sum(vaccinations)', axis=alt.Axis(title='Vaccinations')),    
            tooltip=[alt.Tooltip('sum(vaccinations)', title="# of vaccinations", format=","), 'dose', 'dateWeek'],
            # column='dateWeek',
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
        ).properties(title='All doses by week', height=500)
        st.altair_chart(all_doses_by_week_chart2, use_container_width=True)

        weekday_doses_chart = alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_area().encode(
            x=alt.X('dateWeek', scale=alt.Scale(padding=0)),
            tooltip=[alt.Tooltip('sum(vaccinations)', format=","), 'dayOfWeek', 'date'],
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
    all_df = dt.create_vaccines_dataframe(latest_daily_date)

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
    left, right = st.beta_columns(2)
    with right:
        st.table(summary_df) 

    with left:
        melted_df = all_df.melt(value_vars=["firstDose", "secondDose", "firstDoseCumulative", "secondDoseCumulative", "totalDoses"], id_vars=["date", "areaName"])
        melted_df = melted_df[melted_df.areaName == "United Kingdom"]
        melted_df = melted_df.rename(columns={"value": "vaccinations", "variable": "dose"})

        melted_cumulative_doses = melted_df.loc[(melted_df["dose"] == "firstDoseCumulative") | (melted_df["dose"] == "secondDoseCumulative"), :]
        melted_cumulative_doses.loc[:,"dateWeek"] = pd.to_datetime(melted_cumulative_doses.date).dt.strftime('%Y-%U')

        cumulative_first_doses_chart = alt.Chart(melted_cumulative_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X('dateWeek', axis=alt.Axis(title='Week Ending'), scale=alt.Scale(padding=0)),
            tooltip=['max(vaccinations)'],
            y=alt.Y('max(vaccinations)', axis=alt.Axis(title='Vaccinations')),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom')),
        ).properties(title='Cumulative doses', height=500)
        st.altair_chart(cumulative_first_doses_chart, use_container_width=True)

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    total = dt.total_vaccination_rates(spreadsheet)
    total.loc[:, "%"] = (total.loc[:, "%"] * 100)
    # total.loc[:, "Population"] = total["Population"].map('{:,d}'.format)
    
    st.header("By Age Group")    
    st.table((total.drop(["Age"], axis=1).style
        .format({"Population": "{:,d}", "Vaccinations": "{:,d}", "%": "{:.2f}"})
        # .bar(color='red', vmin=0, subset=['%'], align='left')
        # .bar(color='lightgreen', vmin=0, subset=['Vaccinations'], align='left')
        # .bar(color='lightblue', vmin=0, subset=['Population'], align='left')
        # .set_table_styles({
        #     'Population': [{'selector': '','props': [('width', '200px')]}],
        #     '%': [{'selector': '', 'props': [('background-color', 'black')]}]})
    ))

    left, right = st.beta_columns(2)

    with left:
        total_doses_chart = alt.Chart(total, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            y=alt.Y('Age', sort=["index"]),
            x=alt.X('%', scale=alt.Scale(domain=[0, 100]), title="% of people vaccinated"),    
            tooltip=["Age", alt.Tooltip('%', format='.2f')] 
        ).properties(title="Percentage vaccinated")
        st.altair_chart(total_doses_chart, use_container_width=True)    

    with right:
        total_doses_chart2 = alt.Chart(total, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
            y=alt.Y('Age', sort=["index"]),
            x=alt.X('Vaccinations', title="# of people vaccinated"),    
            tooltip=["Age", alt.Tooltip('Vaccinations')] 
        ).properties(title="People vaccinated")
        st.altair_chart(total_doses_chart2, use_container_width=True)    

def ltla(latest_daily_date, latest_weekly_date):
    st.title("Vaccines Administered by Lower Tier Local Authority")    
    # st.header("All local areas")

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    
    vaccinations = dt.vaccinations_dataframe(spreadsheet)    
    population = dt.population_dataframe(spreadsheet)    
    combined = dt.compute_all_vaccination_rates(vaccinations, population)
    
    # formatting = {column: "{:.2f}" for column in set(combined.columns) - set(["LTLA Code", "LTLA Name"])}

    # st.dataframe(combined.drop(["LTLA Code"], axis=1).style.format(formatting))
    # st.dataframe(vaccinations.drop(["LTLA Code"], axis=1))
    # st.dataframe(population.drop(["LTLA Code"], axis=1))


    # st.header("Specific local area")
    option = st.multiselect('Select local areas:', list(combined["LTLA Name"].values), ["Sutton", "Lewisham", "Solihull"])

    if len(option) > 0:
        local_area = combined.loc[combined["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)
        local_area_absolute = vaccinations.loc[vaccinations["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)
        local_area_population = population.loc[population["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)

        st.subheader("Percentage vaccinated by age group")
        left1, right1 = st.beta_columns(2)
        with right1:
            flipped_local_area = local_area.T
            flipped_local_area.columns = local_area.loc[:, "LTLA Name"]
            flipped_local_area.rename(index={"Under 50": "<50"}, inplace=True)
            formatting = {column: "{:.2f}" for column in set(flipped_local_area.columns) - set(["LTLA Code", "LTLA Name"])}
            st.table(flipped_local_area.drop(["LTLA Name"], axis=0).style.format(formatting))

        with left1:            
            local_area.rename(columns={"Under 50": "<50"}, inplace=True)
            melted_local_area = local_area.melt(value_vars=local_area.columns.drop(["LTLA Name"]), id_vars=["LTLA Name"])
            melted_local_area = melted_local_area.rename(columns={"value": "Percentage", "variable": "Age"})    
            melted_local_area.reset_index(level=0, inplace=True)
            chart = alt.Chart(melted_local_area, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
                y=alt.Y('LTLA Name', sort=["index"], axis=alt.Axis(labels=True, ticks=False), title=None),
                x=alt.X('Percentage', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('LTLA Name', legend=None ),
                row=alt.Row("Age", title=None, sort=["index"]),        
                tooltip=["Age", alt.Tooltip('Percentage', format='.2f')] 
            ).properties()
            make_charts_responsive()
            st.altair_chart(chart, use_container_width=True)  

        st.subheader("People vaccinated by age group")
        left2, right2 = st.beta_columns(2)
        with right2:
            flipped_local_area_absolute = local_area_absolute.T
            flipped_local_area_absolute.columns = local_area_absolute.loc[:, "LTLA Name"]
            flipped_local_area_absolute.rename(index={"Under 50": "<50"}, inplace=True)            
            st.table(flipped_local_area_absolute.drop(["LTLA Name"], axis=0).style.format({column: "{:,}" for column in flipped_local_area_absolute.columns})) 

        with left2:            
            local_area_absolute.rename(columns={"Under 50": "<50"}, inplace=True)
            melted_local_area = local_area_absolute.melt(value_vars=local_area_absolute.columns.drop(["LTLA Name"]), id_vars=["LTLA Name"])
            melted_local_area = melted_local_area.rename(columns={"value": "People Vaccinated", "variable": "Age"})    
            melted_local_area.reset_index(level=0, inplace=True)            
            chart = alt.Chart(melted_local_area, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
                y=alt.Y('LTLA Name', sort=["index"], axis=alt.Axis(labels=True, ticks=False), title=None),
                x=alt.X('People Vaccinated', title="People Vaccinated"),
                color=alt.Color('LTLA Name', legend=None ),
                row=alt.Row("Age", title=None, sort=["index"]),        
                tooltip=["Age", alt.Tooltip('People Vaccinated', format='.2f')] 
            ).properties()
            make_charts_responsive()
            st.altair_chart(chart, use_container_width=True) 

        st.subheader("Population by age group")
        left3, right3 = st.beta_columns(2)
        with right3:
            flipped_local_area_pop = local_area_population.T
            flipped_local_area_pop.columns = local_area_population.loc[:, "LTLA Name"]
            flipped_local_area_pop.rename(index={"Under 50": "<50"}, inplace=True)            
            st.table(flipped_local_area_pop.drop(["LTLA Name"], axis=0).style.format({column: "{:,}" for column in flipped_local_area_absolute.columns})) 

        with left3:            
            local_area_population.rename(columns={"Under 50": "<50"}, inplace=True)
            melted_local_area = local_area_population.melt(value_vars=local_area_population.columns.drop(["LTLA Name"]), id_vars=["LTLA Name"])
            melted_local_area = melted_local_area.rename(columns={"value": "Population", "variable": "Age"})    
            melted_local_area.reset_index(level=0, inplace=True)            
            chart = alt.Chart(melted_local_area, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
                y=alt.Y('LTLA Name', sort=["index"], axis=alt.Axis(labels=True, ticks=False), title=None),
                x=alt.X('Population'),
                color=alt.Color('LTLA Name', legend=None ),
                row=alt.Row("Age", title=None, sort=["index"]),        
                tooltip=["Age", alt.Tooltip('Population', format='.2f')] 
            ).properties()
            make_charts_responsive()
            st.altair_chart(chart, use_container_width=True)       
    else:
        st.write("Select local areas to see the % of people vaccinated")

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
latest_daily_date = parser.parse("2021-04-16")
latest_weekly_date = parser.parse("2021-04-15")
page(latest_daily_date, latest_weekly_date)

st.markdown(f"""- - -
### Data provenance
The data used in this app comes from: 
* [england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations](https://www.england.nhs.uk/statistics/statistical-work-areas/covid-19-vaccinations/) for vaccinations by Local Tier Local Authority and Age Group  
Latest data as of {custom_strftime('{S} %B %Y', latest_weekly_date)}
* [coronavirus.data.gov.uk/details/vaccinations](https://coronavirus.data.gov.uk/details/vaccinations) for total daily vaccinations  
Latest data as of {custom_strftime('{S} %B %Y', latest_daily_date)}
""")

# Scottish data - https://www.opendata.nhs.scot/dataset/covid-19-vaccination-in-scotland/resource/d5ffffc0-f6f3-4b76-8f38-71ccfd7747a4?inner_span=True
    