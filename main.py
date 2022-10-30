import pandas as pd
import copy
import dash
from dash import dcc, html, Input, Output, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# -----------------------------------------------------------------------------------------------------
# LOADING AND PREPARING THE DATA FOR ANALYSIS
# Quelle: https://data.worldbank.org/indicator/SP.DYN.LE00.IN

# loading metadata
metadata = pd.read_csv('/YourFilePathHere/Metadata_File.csv')


# loading data, merging with metadata and creating df for life expectancy for all countries
df_world_raw = pd.read_csv('/YourFilePathHere/LifeExpectancy_File.csv', sep=',', skiprows=3)
df_world = copy.deepcopy(df_world_raw)
df_world = pd.merge(left=df_world, right=metadata, on='Country Code', how='inner')
df_world = df_world.drop(['Unnamed: 5', 'TableName', 'SpecialNotes', 'Unnamed: 66', 'Indicator Code',
                          'Indicator Name', '2021'], axis=1).reset_index()
df_world.at[258, 'Region'] = 'World'
# df_world shall only contain countries and not regions
df_world = df_world[df_world['Region'].notna()]


# loading data, merging with metadata and creating df for life expectancy for male population
raw_life_exp_males = pd.read_csv('/YourFilePathHere/LifeExpectancy_Males_File.csv', sep=',', skiprows=3)
life_exp_males = copy.deepcopy(raw_life_exp_males)
life_exp_males = pd.merge(left=life_exp_males, right=metadata, on='Country Code', how='inner')
life_exp_males = life_exp_males.drop(['Unnamed: 5', 'TableName', 'SpecialNotes', 'Unnamed: 66', 'Indicator Code',
                                      'Indicator Name', '2021'], axis=1).reset_index()
life_exp_males.at[258, 'Region'] = 'World'
life_exp_males = life_exp_males[life_exp_males['Region'].notna()]


# loading data, merging with metadata and creating df for life expectancy for female population
raw_life_exp_females = pd.read_csv('/YourFilePathHere/LifeExpectancy_Females_File.csv', sep=',', skiprows=3)
life_exp_females = copy.deepcopy(raw_life_exp_females)
life_exp_females = pd.merge(left=life_exp_females, right=metadata, on='Country Code', how='inner')
life_exp_females = life_exp_females.drop(['Unnamed: 5', 'TableName', 'SpecialNotes', 'Unnamed: 66', 'Indicator Code',
                                          'Indicator Name', '2021'], axis=1).reset_index()
life_exp_females.at[258, 'Region'] = 'World'
life_exp_females = life_exp_females[life_exp_females['Region'].notna()]


# converting all loaded dataframes to long-format dataframes and merging them to a single df
year = [str(i+1960) for i in range(61)]
column_names = ['Country Name', 'Country Code', 'Region', 'IncomeGroup']
column_names_global = ['Country Name', 'Country Code']

df_world = pd.melt(df_world, id_vars=column_names, value_vars=year)
df_world = df_world.rename(columns={'variable': 'year'})
df_world = df_world.rename(columns={'value': 'life_expectancy_avg'})

df_male = pd.melt(life_exp_males, id_vars=column_names, value_vars=year)
df_male = df_male.rename(columns={'variable': 'year'})
df_male = df_male.rename(columns={'value': 'life_expectancy_males'})

df_female = pd.melt(life_exp_females, id_vars=column_names, value_vars=year)
df_female = df_female.rename(columns={'variable': 'year'})
df_female = df_female.rename(columns={'value': 'life_expectancy_females'})

df = pd.merge(left=df_world, right=df_male, on=['Country Name', 'Country Code', 'Region', 'IncomeGroup', 'year'],
              how='left')
df = pd.merge(left=df, right=df_female, on=['Country Name', 'Country Code', 'Region', 'IncomeGroup', 'year'],
              how='left')
df['year'] = df['year'].astype(int)


# -----------------------------------------------------------------------------------------------------
# EXPLORATORY ANALYSIS

# calculating the deviation of life expectancy from the global average for each country
# adapting and expanding the df accordingly
df_global = df[df['Country Code'] == 'WLD']
df = pd.merge(left=df, right=df_global[['year', 'life_expectancy_avg']], on=['year'], how='left')
df['deviation_from_global_avg'] = df['life_expectancy_avg_x']-df['life_expectancy_avg_y']
df = df.drop(['life_expectancy_avg_y'], axis=1).reset_index()
df = df.rename(columns={'life_expectancy_avg_x': 'life_expectancy_avg'})


# getting the min and max life expectancy and country for the years 1960 and 2020
# 1960: min 28.199 in Mali and max 73.549756 in Norway
# 2020: min 53.679 in Central African Republic and max 85.387805 in Hong Kong
df_1960 = df[df['year'] == 1960]
min_1960 = df_1960[df_1960['life_expectancy_avg'] == df_1960['life_expectancy_avg'].min()]
max_1960 = df_1960[df_1960['life_expectancy_avg'] == df_1960['life_expectancy_avg'].max()]

df_2020 = df[df['year'] == 2020]
min_2020 = df_2020[df_2020['life_expectancy_avg'] == df_2020['life_expectancy_avg'].min()]
max_2020 = df_2020[df_2020['life_expectancy_avg'] == df_2020['life_expectancy_avg'].max()]


# -----------------------------------------------------------------------------------------------------
# APP LAYOUT

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])

app.layout = dbc.Container(html.Div([

    dbc.Row(
        dbc.Col(html.Div([
            html.H1('Life Expectancy Dashboard', style={'text-align': 'center', 'marginTop': 55, 'color': '#2c3e50'}),
        ]), width=12)
    ),

    dbc.Row(dbc.Col(html.Div([
        html.H3("How did Life Expectancy Change Across the Globe?", style={'paddingTop': 50, 'color': '#084081'}),
        html.H5("IN THIS SECTION YOU CAN: compare countries with each other", style={'color': '#2b8cbe'}),
        html.Hr(style={'color': "#2b8cbe", 'paddingBottom': 10, 'marginBottom': 50})
    ]))),

    dbc.Row(
            [
                dbc.Col(html.Div([
                    html.Div("Life expectancy tells us a lot about the state of a society and is a key metric worth "
                             "studying. This is why the world map shows the latest data published by the World Bank "
                             "for 'life expectancy at birth', measured in years. This metric indicates"
                             "the number of years a newborn infant would live if current mortality trends at the"
                             "time of its birth were to persist throughout its life."),
                    html.Br(),
                    html.Div("Since industrialization, life expectancy has steadily improved worldwide. "
                             "In this analysis, we look at the last few decades, from 1960 to 2020. "),
                    html.Br(),
                    html.Div(
                             "Hover over any country to view the changing life expectancy there, "
                             "or use the slider to see the change through time below the map.",
                        style={"font-weight": "bold"})]), width=3),

                # interactive map incl. slider
                dbc.Col(html.Div([
                    html.H5("Improvement in Global Life Expectancy over Time"),
                    html.H6("Life expectancy increased from 1960 to 2020 from a global average "
                            "of around 52 years to over 72 years.", style={"color": '#95a5a6'}),
                    html.Br(),
                    dcc.Graph(id="graph-with-slider", hoverData={'points': [{'customdata': 'WLD'}]}),
                    dcc.Slider(
                        min=df['year'].min(),
                        max=df['year'].max(),
                        step=None,
                        marks={
                            1960: '1960',
                            1965: '1965',
                            1970: '1970',
                            1975: '1975',
                            1980: '1980',
                            1985: '1985',
                            1990: '1990',
                            1995: '1995',
                            2000: '2000',
                            2005: '2005',
                            2010: '2010',
                            2015: '2015',
                            2020: '2020'
                        },
                        value=df['year'].max(),
                        id='year-slider',
                        tooltip={"placement": "bottom", "always_visible": True})
                        ]), width={"size": 8, "offset": 1})
            ]
        ),

    dbc.Row([
        dbc.Col(html.Div([
            # line chart comparing countries incl. drop-down menu
            html.H5("Differences in Life Expectancy between Countries", style={'text-align': 'left'}),
            html.H6("Despite increasing life expectancy around the world, there are still differences between "
                    "countries.", style={"text-align": "left", "color": '#95a5a6'}),
            html.Div([dcc.Dropdown(
                id='dropdown',
                options=df['Country Name'],
                multi=True,
                value=['World'],
                placeholder='Select one or more countries',
            )], style={'width': '40%'}),
            html.Br(),
            dcc.Graph(id="line-chart-countries"),
        ]), width=8),
        # accompanying text
        dbc.Col(html.Div([
            html.Div("Differences in life expectancy between nations still exist, but these differences have narrowed "
                     "over the past 60 years."),
            html.Br(),
            html.Div("For example, the lowest life expectancy in 1960 was around 28 years "
                     "(Mali). In comparison, the highest was about 73.5 years (Norway). Today, the lowest life "
                     "expectancy in 2020 is around 53.7 years (Central African Republic), and the highest is "
                     "85.4 years (Hong Kong)."),
            html.Br(),
            html.Div("Explore the differences between countries by selecting them from the drop-down menu.")]), width=4)
    ], style={"marginTop": 80}),

    dbc.Row(dbc.Col(html.Div([
        html.H3("How did Life Expectancy Change In Your Selected Country?",
                style={'paddingTop': 50, 'color': '#084081'}),
        html.H5("IN THIS SECTION YOU CAN: get a deep dive into your selected country", style={'color': '#2b8cbe'}),
        html.Hr(style={'color': "#2b8cbe", 'paddingBottom': 10, 'marginBottom': 50})
    ]))),

    dbc.Row(
            [
                # line chart showing life expectancy numbers for female and male population
                dbc.Col(html.Div([html.H5("A Comparison between Male & Female Population"),
                                  html.H6("Life expectancy of women is on average higher than that of men.",
                                          style={"color": '#95a5a6'}),
                                  dcc.Graph(id="line-chart")
                                  ]), width=8),
                # data card / indicator showing the growth rate
                dbc.Col(html.Div([
                    html.Div("How much did a country's life expectancy grow from 1960 to 2020? "
                             "This question is answered by the growth rate shown for the various population groups. "
                             "African countries in particular have recorded high overall growth in life expectancy. "
                             ),
                    html.Br(),
                    html.H5("Growth Rate of Life Expectancy"),
                    html.H6("The overall growth differs between the male, female and average "
                            "population of a country.", style={"color": '#95a5a6'}),
                    html.Br(),
                    dcc.Graph(id='indicator'),
                    html.Br(),
                    dbc.Button('Total Population', id='btn_1', n_clicks=0, outline=True, color="secondary",
                               size="sm", style={'margin': 7}),
                    dbc.Button('Female Population', id='btn_2', n_clicks=0, outline=True, color="secondary",
                               size="sm", style={'margin': 7}),
                    dbc.Button('Male Population', id='btn_3', n_clicks=0, outline=True, color="secondary",
                               size="sm", style={'margin': 7}),

                ]), width=4)
            ],
    ),

    dbc.Row(
        [
            dbc.Col(html.Div([
                "Global life expectancy is rising - but how far off is the selected country in comparison? "
                "The absolute deviation of life expectancy in years from the global average shows how far above or "
                "below average the country's life expectancy is. It shows that more and more countries are coming "
                "closer to the global life expectancy, with Western countries almost always above it and African "
                "countries in particular still below the global average."]), width=3),
            # bar chart showing deviation from global average life expectancy
            dbc.Col(html.Div([
                html.H5("Absolute Deviation of Life Expectancy in Years from the Global Average"),
                html.H6("Over time, countries' life expectancies converge to the global average. ",
                        style={"color": '#95a5a6'}),
                html.Br(),
                dcc.Graph(id="bar-chart")
            ]), width={"size": 8, "offset": 1})
        ], style={"marginTop": 60}
    ),

    dbc.Row(
        dbc.Col([
            html.Br(),
            html.P('© Kathrin Hälbich, 2022',
                   style={'text-align': 'center', 'marginTop': 80,
                          'paddingBottom': 50, 'color': '#D6DBDF'})
        ])
    )


]))


# -----------------------------------------------------------------------------------------------------
# CONNECT THE GRAPHS WITH DASH COMPONENTS AND ALLOW INTERACTIVITY


# interactive world map - choropleth map
@app.callback(
    Output(component_id='graph-with-slider', component_property='figure'),
    [Input(component_id='year-slider', component_property='value')]
)
def update_figure(selected_year):
    color_scale = ['#ffffff', '#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4', '#4eb3d3', '#2b8cbe',
                   '#0868ac', '#084081']
    # reaction of the map to moving the slider to a different year
    filtered_df = df[df.year == selected_year].reset_index()

    # creation and layout of choropleth map
    world_map = px.choropleth(filtered_df, locations=filtered_df['Country Code'], locationmode='ISO-3',
                              color=filtered_df.life_expectancy_avg,
                              color_continuous_scale=color_scale,
                              labels={'life_expectancy_avg': 'Avg. Life Expectancy'},
                              range_color=(0, 95),
                              hover_name='Country Name',
                              hover_data={'Country Code': False},
                              basemap_visible=False)
    world_map.update_layout(transition_duration=500,
                            margin=dict(l=0, r=0, b=0, t=0),
                            width=1000,
                            height=400)
    return world_map


# line chart comparing countries incl. drop-down menu
@app.callback(
    Output(component_id='line-chart-countries', component_property='figure'),
    [Input(component_id='graph-with-slider', component_property='hoverData'),
     Input(component_id='dropdown', component_property='value')]
)
def update_line_chart_countries(hoverData, country_list):
    color_scale = ['#d5405e', '#a6cee3', '#1f78b4', '#ffb3a7', '#b2df8a', '#00429d', '#33a02c']

    # process information of hover feature and drop-down
    country_code = hoverData['points'][0]['customdata']
    country_code = "".join(str(x) for x in country_code)
    df_hover = df[df['Country Code'] == country_code]
    df_dropdown = df[(df['Country Name'].isin(country_list))]
    new_df = pd.concat([df_hover, df_dropdown]).drop_duplicates()

    # creation and layout of line chart
    line_chart_countries = px.line(new_df, x=new_df['year'], y=new_df['life_expectancy_avg'],
                                   color=new_df['Country Name'],
                                   hover_data={'Country Name': False},
                                   color_discrete_sequence=color_scale)
    line_chart_countries.update_xaxes(title='Years', linecolor="#343a40", showticklabels=True, ticks='outside')
    line_chart_countries.update_yaxes(title='Average Life Expectancy', linecolor="#343a40", showticklabels=True,
                                      ticks='outside')
    line_chart_countries.update_layout(hovermode='x', plot_bgcolor="white",
                                       legend=dict(orientation="h", yanchor="bottom",
                                                   y=1.02,
                                                   xanchor="right",
                                                   x=1,
                                                   bordercolor='#ccc', borderwidth=1,
                                                   title=" Selected Countries: "))
    line_chart_countries.update_traces(line_width=2, hovertemplate=None)
    return line_chart_countries


# line chart showing life expectancy numbers for female and male population
@app.callback(
    Output(component_id='line-chart', component_property='figure'),
    [Input(component_id='graph-with-slider', component_property='hoverData')]
)
def update_line_chart(hoverData):
    color_scale = ['#c5d0d6', '#084081', '#d5405e']
    list_of_names = ['Total Population', 'Male Population', 'Female Population']

    # process information of hover feature
    country_code = hoverData['points'][0]['customdata']
    country_code = "".join(str(x) for x in country_code)
    dff = df[df['Country Code'] == country_code]

    # creation and layout of line chart
    line_chart = px.line(dff, x=dff['year'], y=dff.columns[6:9], color_discrete_sequence=color_scale)
    line_chart.update_layout(plot_bgcolor='white',
                             hovermode='x',
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                         bordercolor='#ccc', borderwidth=1, title="Average Life Expectancy of: "))
    line_chart.update_traces(line_width=2, hovertemplate=None)
    line_chart.update_xaxes(title='Years', linecolor="#343a40", showticklabels=True, ticks='outside')
    line_chart.update_yaxes(title='Average Life Expectancy', linecolor="#343a40", showticklabels=True, ticks='outside')
    # changing the label names
    for idx, name in enumerate(list_of_names):
        line_chart.data[idx].name = name
    return line_chart


# data card / indicator showing the growth rate
@app.callback(
    Output(component_id='indicator', component_property='figure'),
    [Input(component_id='graph-with-slider', component_property='hoverData'),
     Input(component_id='btn_1', component_property='n_clicks'),
     Input(component_id='btn_2', component_property='n_clicks'),
     Input(component_id='btn_3', component_property='n_clicks')]
)
def update_indicator(hoverData, btn_1, btn_2, btn_3):
    # process information of hover feature
    country_code = hoverData['points'][0]['customdata']
    country_code = "".join(str(x) for x in country_code)
    df_indicator = df[df['Country Code'] == country_code]

    # finding max and min value in selected country to calculate growth rate
    df_indicator_max = df_indicator.loc[df_indicator['year'] == df_indicator['year'].max()].reset_index(drop=True)
    df_indicator_min = df_indicator.loc[df_indicator['year'] == df_indicator['year'].min()].reset_index(drop=True)
    max_value = df_indicator_max.loc[0, 'life_expectancy_avg']
    min_value = df_indicator_min.loc[0, 'life_expectancy_avg']

    # process information of button clicked (female, male, or total population)
    changed_btn = ctx.triggered[0]['prop_id'].split('.')[0]

    if changed_btn == 'btn_1':
        max_value = df_indicator_max.loc[0, 'life_expectancy_avg']
        min_value = df_indicator_min.loc[0, 'life_expectancy_avg']
    elif changed_btn == 'btn_2':
        max_value = df_indicator_max.loc[0, 'life_expectancy_females']
        min_value = df_indicator_min.loc[0, 'life_expectancy_females']
    elif changed_btn == 'btn_3':
        max_value = df_indicator_max.loc[0, 'life_expectancy_males']
        min_value = df_indicator_min.loc[0, 'life_expectancy_males']

    # creating figure
    fig = go.Figure(go.Indicator(
        mode='delta',
        value=max_value,
        delta={'reference': min_value, 'relative': True, 'valueformat': '.2%'},
        ))
    fig.update_layout(paper_bgcolor='white', margin=dict(l=0, r=0, b=0, t=0), height=60)
    return fig


# bar chart showing deviation from global average life expectancy
@app.callback(
    Output(component_id='bar-chart', component_property='figure'),
    [Input(component_id='graph-with-slider', component_property='hoverData')]
)
def update_bar_chart(hoverData):
    # process information of hover feature
    country_code = hoverData['points'][0]['customdata']
    country_code = "".join(str(x) for x in country_code)
    dff_bar = df[df['Country Code'] == country_code].reset_index()
    dff_bar['color'] = np.where(dff_bar['deviation_from_global_avg'] < 0, '#d5405e', '#a8ddb5')

    # creation and layout of bar chart
    bar_chart = px.bar(dff_bar, x='year', y=dff_bar['deviation_from_global_avg'].round(decimals=1))
    bar_chart.update_layout(yaxis_range=[-20, 20], margin=dict(l=0, r=0, b=0, t=0), height=250, plot_bgcolor='white')
    bar_chart.update_traces(marker_color=dff_bar['color'], hovertemplate=None)
    bar_chart.update_xaxes(title='Years', linecolor="#343a40", showticklabels=True, ticks='outside')
    bar_chart.update_yaxes(title='Deviation from Global Average', linecolor="#343a40", showticklabels=True,
                           ticks='outside')

    # add a horizontal "zero" line
    bar_chart.add_shape(type="line", line_color="black", line_width=1, opacity=1, line_dash="dot", x0='1960', y0=0,
                        x1='2022', y1=0)
    return bar_chart


if __name__ == '__main__':
    app.run_server(debug=True)
