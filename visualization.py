import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

# Read combined data
df = pd.read_csv('combined_data_source.csv')

# Drop columns that are not needed for cluster collapsing
df_reduced = df.drop(['Property Name', 'Deal Id', 'Project Id', 'NCE', 'NCE per Desk', 'NCE per USF'], axis=1)

# Get separate df's for each year
df16_reduced = df_reduced[df_reduced['Open Year'] == 2016]
df17_reduced = df_reduced[df_reduced['Open Year'] == 2017]

# Collapse clusters
collapsed_df = df_reduced.groupby(['Cluster']).sum()
collapsed_df16 = df16_reduced.groupby(['Cluster']).sum()
collapsed_df17 = df17_reduced.groupby(['Cluster']).sum()

# Calculate NCE, NCE per Desk, and NCE per USF
for i in [collapsed_df16, collapsed_df17, collapsed_df]:
    i['NCE'] = i['Capital Expenditure'] - i['TI Monies Received']
    i['NCE per Desk'] = i['NCE'] / i['Desk Count']
    i['NCE per USF'] = i['NCE'] / i['USF']

# Start building viz
app = dash.Dash()

app.layout = html.Div([
dcc.Markdown('''
# Case Study Submission
*An analysis of Net Capital Expenditure by market and cluster during 2016 and 2017*

By: Afaan Naqvi
***
### 1. Cluster Analysis (2016 vs 2017)
'''),
    html.Div([
        html.Div([
            dcc.Graph(
                id='nce-desk-year',
                figure={
                'data': [
                {'x': [i for i in collapsed_df16.index], 'y':[i for i in collapsed_df16['NCE per Desk']], 'type': 'bar', 'name': '2016'},
                {'x': [i for i in collapsed_df17.index], 'y':[i for i in collapsed_df17['NCE per Desk']], 'type': 'bar', 'name': '2017'},
                ],
                'layout': {
                'title': 'NCE per Desk',
                'yaxis':{
                'title': 'US$/Desk'}

                }
                }
                )
            ],
            style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(
                id='nce-usf-year',
                figure={
                'data': [
                {'x': [i for i in collapsed_df16.index], 'y':[i for i in collapsed_df16['NCE per USF']], 'type': 'bar', 'name': '2016'},
                {'x': [i for i in collapsed_df17.index], 'y':[i for i in collapsed_df17['NCE per USF']], 'type': 'bar', 'name': '2017'},
                ],
                'layout': {
                'title': 'NCE per USF',
                'yaxis':{
                'title': 'US$/USF'}
                }
                }

                )
            ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ]),

    html.Hr(),
    
dcc.Markdown('''
### 2. Intra-Cluster Analysis (2016 through 2017)
'''),
    html.Div([
        html.Div([
            dcc.Graph(
                id='nce-desk-cluster',
                figure={
                'data': [
                {'x': [i for i in collapsed_df.index], 'y':[i for i in collapsed_df['NCE per Desk']], 'type': 'bar'},
                ],
                'layout': {
                'title': 'NCE per Desk',
                'yaxis':{
                'title': 'US$/Desk'}

                }
                }
                )
            ],
            style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(
                id='nce-usf-cluster',
                figure={
                'data': [
                {'x': [i for i in collapsed_df.index], 'y':[i for i in collapsed_df['NCE per USF']], 'type': 'bar'},
                ],
                'layout': {
                'title': 'NCE per USF',
                'yaxis':{
                'title': 'US$/USF'}
                }       
                }   

                )
            ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ]),    

    html.Hr(),
    
dcc.Markdown('''
### 3. Market Analysis
'''),
    html.Div([
        html.Div([
            dcc.Graph(
                id='nce-desk-market',
                figure={
                'data': [
                {'x': [i for i in collapsed_df.index], 'y':[i for i in collapsed_df['NCE per Desk']], 'type': 'bar'},
                ],
                'layout': {
                'title': 'NCE per Desk',
                'yaxis':{
                'title': 'US$/Desk'}

                }
                }
                )
            ],
            style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(
                id='nce-usf-market',
                figure={
                'data': [
                {'x': [i for i in collapsed_df.index], 'y':[i for i in collapsed_df['NCE per USF']], 'type': 'bar'},
                ],
                'layout': {
                'title': 'NCE per USF',
                'yaxis':{
                'title': 'US$/USF'}
                }
                }

                )
            ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ]),  
    
    html.Hr(),
    
dcc.Markdown('''
### 4. Outlier Analysis
'''),
    html.Div([
        dcc.Graph(
            id='nce-scatter',
            figure={
            'data': [
            go.Scatter(
                x=df[df['Cluster'] == i]['NCE per Desk'],
                y=df[df['Cluster'] == i]['NCE per USF'],
                text=df[df['Cluster'] == i]['Market'],
                mode='markers',
                opacity=0.7,
                marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
                },
                name=i
                ) for i in df['Cluster'].unique()
            ],
            'layout': go.Layout(
                xaxis={'title': 'US$/Desk'},
                yaxis={'title': 'US$/USF'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                hovermode='closest',
                )
            }
            )
        ]),   
    
    
    dcc.Markdown('''
        ''')
    ])

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
    app.run_server()