import streamlit as st

import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
from utils import suffix, custom_strftime, make_charts_responsive
import data as dt
import st_data as sdt

def daily(latest_daily_date, latest_weekly_date):
    all_df = sdt.create_vaccines_dataframe(latest_daily_date).copy()
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
    melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses", "oneWeekAgo"] = melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses"]["vaccinations"].shift(periods=7)
    melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses", "oneWeekAgoDiff"] = melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses"]["vaccinations"].diff(periods=7)
    melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses", "oneWeekAgoPercentage"] = melted_daily_doses.loc[melted_daily_doses.dose == "totalDoses"]["vaccinations"].pct_change(periods=7)*100


    melted_daily_doses.loc[:, "dayOfWeek"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%A"))
    melted_daily_doses.loc[:, "dayOfWeekIndex"] = melted_daily_doses.date.apply(lambda item: parser.parse(item).strftime("%w"))

    melted_first_second_daily_doses = melted_daily_doses.loc[(melted_daily_doses.dose.isin(["firstDose", "secondDose"]))]

    melted_total_doses = melted_daily_doses.loc[(melted_daily_doses.dose.isin(["totalDoses"]))]

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
        st.header("All doses by day")
        rolling_average_chart = (alt.Chart(melted_first_second_daily_doses, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends)),
            tooltip=[alt.Tooltip('vaccinations', format=",.0f"), "date"],
            y=alt.Y('vaccinations', axis=alt.Axis(title='Doses')),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
            )
        .properties(height=500))

        st.altair_chart(rolling_average_chart, use_container_width=True)

    left2, right2 = st.beta_columns(2)
    with left2:    
        st.header("7-day rolling average")
        rolling_average_chart = (alt.Chart(melted_daily_doses.loc[~pd.isna(melted_daily_doses.rollingAverage)]).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends)),
            tooltip=[alt.Tooltip('rollingAverage', format=",.0f"), "date"],
            y=alt.Y('rollingAverage', axis=alt.Axis(title='Doses')),
            color=alt.Color('dose', legend=alt.Legend(orient='bottom'))
            )
        .properties(height=500))
        bank_holidays = ["2021-04-02", "2021-04-05", "2021-05-03"]
        line = alt.Chart(pd.DataFrame({'x': bank_holidays})).mark_rule(strokeDash=[10,10], color="#85929e").encode(x='x')
        st.altair_chart(alt.layer(rolling_average_chart, line, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}), use_container_width=True)

    with right2:
        st.header("% of first doses by day")
        percentage_doses_chart = (alt.Chart(all_df, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_line(point=True).encode(
            x=alt.X("date", axis=alt.Axis(values=weekends), scale=alt.Scale(padding=0)),
            tooltip=[alt.Tooltip('mean(percentageFirstDose)', title="% of first dose", format=".2f"), "date"],
            y=alt.Y('mean(percentageFirstDose)', axis=alt.Axis(title='% first dose')))
            .properties(height=500))
        st.altair_chart(percentage_doses_chart, use_container_width=True)        

    left3, right3 = st.beta_columns(2)
    with left3:
        st.header("Change vs same day last week")
        chart = (alt.Chart(melted_total_doses.loc[~pd.isna(melted_daily_doses.rollingAverage)], padding={"left": 10, "top": 10, "right": 10, "bottom": 10})
                    .mark_bar(point=True)
                    .encode(
                        x=alt.X("date", axis=alt.Axis(values=weekends)),
                        tooltip=["date", 
                            alt.Tooltip('vaccinations', title="Today", format=","), 
                            alt.Tooltip('oneWeekAgo', title="Last week on this day", format=","),
                            alt.Tooltip('oneWeekAgoDiff', title="Absolute change", format=","),
                            alt.Tooltip('oneWeekAgoPercentage', title="% change", format=",.2f")                        
                            ],
                        y=alt.Y('oneWeekAgoPercentage', axis=alt.Axis(title='% change'), impute={'value': 0}),
                        color=alt.condition(alt.datum.oneWeekAgoPercentage > 0, alt.value("green"),  alt.value("red"))
                        ).properties(height=500))

        st.altair_chart(chart, use_container_width=True)

def weekly(latest_daily_date, latest_weekly_date):
    all_df = sdt.create_vaccines_dataframe(latest_daily_date).copy()
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
    all_df = sdt.create_vaccines_dataframe(latest_daily_date)

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
    to_append = pd.DataFrame([{
        "Vaccinations": total["Vaccinations"].sum().astype("int64"), 
        "Population": total["Population"].sum().astype("int64"),
        "Age": "Overall",
        "%": 100 * (total["Vaccinations"].sum().astype("int64") / total["Population"].sum().astype("int64"))
        }
    ], index = ["Overall"])

    total_overall = total.append(to_append)
    st.table((total_overall.drop(["Age"], axis=1).style
        .format({"Population": "{:,d}", "Vaccinations": "{:,d}", "%": "{:.2f}"})
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


def create_region_map(regions, vaccination_rates_by_region, field):
    # schemes - https://vega.github.io/vega/docs/schemes/#reference
    # chart = alt.Chart(regions, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_geoshape(
    chart = alt.Chart(regions).mark_geoshape(
                stroke='white',
                strokeWidth=2
            ).encode(
                tooltip=["Region:N", alt.Tooltip(f"{field}:Q", title="% vaccinated", format=".2f")],
                # color="#efe",
                color = alt.Color(f"{field}:Q", scale=alt.Scale(scheme="blues"), legend=alt.Legend(title=None))
            ).transform_lookup(
                lookup='properties.EER13NM',
                from_=alt.LookupData(
                    data=vaccination_rates_by_region, 
                    key='Region', 
                    fields=list(vaccination_rates_by_region.columns))
            ).properties(height=500, title=f"Vaccination Rates: {field}")

    labels = alt.Chart(regions).mark_text(baseline='top', color='#E67E22', fontWeight=800).properties(
        width=400,
        height=400
     ).encode(
         longitude='properties.centroid_lon:Q',
         latitude='properties.centroid_lat:Q',
         text='properties.EER13NM:O',
         size=alt.value(10),
         opacity=alt.value(100)
     )

    return alt.layer(chart, labels, padding={"left": 10, "top": 10, "right": 10, "bottom": 10})

def region(latest_daily_date, latest_weekly_date):
    st.title("Vaccines Administered by Region")

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    
    vaccinations = sdt.vaccinations_dataframe(spreadsheet)    
    population = sdt.population_dataframe(spreadsheet)
    population = population.merge(vaccinations[["UTLA Name", "Region Name (administrative)", "LTLA Code"]], 
                              left_on="LTLA Code", right_on="LTLA Code")

    population_by_region = population.groupby(["Region Name (administrative)"]).sum()
    population_by_region.insert(0, "Region", list(population_by_region.index))
    population_by_region.loc[:, "Overall"] = population_by_region.sum(axis=1).astype("int64")

    vaccinations_by_region = vaccinations.groupby(["Region Name (administrative)"]).sum()
    vaccinations_by_region.insert(0, "Region", list(vaccinations_by_region.index))
    vaccinations_by_region.loc[:, "Overall"] = vaccinations_by_region.sum(axis=1).astype("int64")

    vaccination_rates_by_region = ((vaccinations_by_region
        .select_dtypes(exclude='object')
        .div(population_by_region.select_dtypes(exclude='object')) * 100)
        .combine_first(vaccinations_by_region)[vaccinations_by_region.columns])

    vaccination_rates_by_region.loc[:, "Overall"] = vaccinations_by_region["Overall"].div(population_by_region["Overall"]) * 100

    age_groups = list(vaccination_rates_by_region.drop(["Region"], axis=1).columns)

    regions = alt.topo_feature("https://raw.githubusercontent.com/mneedham/covid-vaccines/main/data/topo_eer.json", 'eer')
    # regions = alt.topo_feature("http://localhost:8000/data/topo_eer.json", 'eer')


    left, right = st.beta_columns(2)    
    with left:
        for field in [f for idx, f in enumerate(age_groups) if idx % 2 == 0]:
            with st.spinner("Loading map..."):
                background = create_region_map(regions, vaccination_rates_by_region, field)
                st.altair_chart(background, use_container_width=True)

    with right:
        for field in [f for idx, f in enumerate(age_groups) if idx % 2 != 0]:
            background = create_region_map(regions, vaccination_rates_by_region, field)
            st.altair_chart(background, use_container_width=True) 

def by_ltla(latest_daily_date, latest_weekly_date):
    st.title("Vaccines Administered by Lower Tier Local Authority")    

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    vaccinations = sdt.vaccinations_dataframe(spreadsheet)    
    population = sdt.population_dataframe(spreadsheet)    
    combined = dt.compute_all_vaccination_rates(vaccinations, population)
    combined.loc[:, "Overall"] = 100 * (vaccinations.sum(axis=1).astype("int64") / population.sum(axis=1).astype("int64"))

    left,right = st.beta_columns(2)
    with left:
        st.header("Overall vaccination rate by region")
        chart = alt.Chart(combined, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_boxplot().encode(
            y='Region Name (administrative):O',
            x=alt.Y('Overall:Q',scale = alt.Scale(domain=[0,100]))
        ).properties(height=500)
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.header("Population by region")
        population_with_regions = population.copy()
        population_with_regions = population_with_regions.merge(vaccinations[["UTLA Name", "Region Name (administrative)", "LTLA Code"]], 
                              left_on="LTLA Code", right_on="LTLA Code")
        population_with_regions.loc[:, "Overall"] = population_with_regions.sum(axis=1)
        # st.write(population_with_regions)
        chart = alt.Chart(population_with_regions, padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).transform_aggregate(
            sum_overall='sum(Overall)',
            sum_under_45='sum(Under 40)',
            groupby=['Region Name (administrative)']
        ).transform_calculate(
            under45s='100 * (datum.sum_under_45 / datum.sum_overall)'
        ).mark_bar(color="#2E4053").encode(
            x='Region Name (administrative)',
            tooltip=["under45s:Q"],
            y=alt.Y('under45s:Q', title="Population under 40")
        ).properties(height=500)
        st.altair_chart(chart, use_container_width=True)

    left2, right2 = st.beta_columns(2)

    with left2:
        st.header("Least vaccinated areas")
        worst = combined.sort_values(["Overall"]).head(20)
        chart = alt.Chart(worst.sort_values(["Overall"]), padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
                x=alt.Y('LTLA Name:O', sort='y'),
                color=alt.Color('Region Name (administrative)', legend=alt.Legend(orient='top')),
                tooltip=["LTLA Name", "Overall"],
                y=alt.X('Overall:Q',scale = alt.Scale(domain=[0,100]))
            ).properties(height=500, title="Least vaccinated areas")
        st.altair_chart(chart, use_container_width=True)
    
    with right2:
        st.header("Most vaccinated areas")
        best = combined.sort_values(["Overall"], ascending=False).head(20)
        chart = alt.Chart(best.sort_values(["Overall"]), padding={"left": 10, "top": 10, "right": 10, "bottom": 10}).mark_bar().encode(
                x=alt.Y('LTLA Name:O', sort='-y'),
                color=alt.Color('Region Name (administrative)', legend=alt.Legend(orient='top', columns=4)),
                tooltip=["LTLA Name", "Overall"],
                y=alt.X('Overall:Q',scale = alt.Scale(domain=[0,100]))
            ).properties(height=500, title="Most vaccinated areas")
        st.altair_chart(chart, use_container_width=True)

def my_ltla(latest_daily_date, latest_weekly_date):
    st.title("Vaccines Administered by selected Lower Tier Local Authorities")    

    spreadsheet = f"data/COVID-19-weekly-announced-vaccinations-{latest_weekly_date.strftime('%-d-%B-%Y')}.xlsx"
    
    vaccinations = sdt.vaccinations_dataframe(spreadsheet)    
    population = sdt.population_dataframe(spreadsheet)    
    combined = dt.compute_all_vaccination_rates(vaccinations, population)

    option = st.multiselect('Select local areas:', list(combined["LTLA Name"].values), ["Sutton", "Lewisham", "Solihull"])
    columns_to_drop = ["LTLA Name", "UTLA Code", "UTLA Name", "Region Code (Administrative)", "Region Name (administrative)"]
    if len(option) > 0:
        local_area = combined.loc[combined["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)
        local_area_absolute = vaccinations.loc[vaccinations["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)
        local_area_population = population.loc[population["LTLA Name"].isin(option)].drop(["LTLA Code"], axis=1)

        st.subheader("Percentage vaccinated by age group")
        left1, right1 = st.beta_columns(2)
        with right1:            
            flipped_local_area = local_area.T
            flipped_local_area.columns = local_area.loc[:, "LTLA Name"]
            flipped_local_area.rename(index={"Under 45": "<45"}, inplace=True)
            formatting = {column: "{:.2f}" for column in set(flipped_local_area.columns) - set(columns_to_drop)}
            st.table(flipped_local_area.drop(columns_to_drop, axis=0).style.format(formatting))

        with left1:            
            local_area.rename(columns={"Under 45": "<45"}, inplace=True)
            melted_local_area = local_area.melt(value_vars=local_area.columns.drop(columns_to_drop), id_vars=["LTLA Name"])
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
            flipped_local_area_absolute.rename(index={"Under 45": "<45"}, inplace=True)            
            st.table(flipped_local_area_absolute.drop(columns_to_drop, axis=0).style.format({column: "{:,}" for column in flipped_local_area_absolute.columns})) 

        with left2:            
            local_area_absolute.rename(columns={"Under 45": "<45"}, inplace=True)
            melted_local_area = local_area_absolute.melt(value_vars=local_area_absolute.columns.drop(columns_to_drop), id_vars=["LTLA Name"])
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
    "By Region": region,
    "By Local Authority": by_ltla,
    "My Local Authority": my_ltla
}

alt.themes.enable('fivethirtyeight')
st.set_page_config(layout="wide")
st.sidebar.title("UK Coronavirus Vaccines")

radio_list = list(PAGES.keys())
selection = st.sidebar.radio("Select Dashboard", radio_list)

page = PAGES[selection]

population = 68134973
latest_daily_date = parser.parse("2021-05-16")
latest_weekly_date = parser.parse("2021-05-13")
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
    