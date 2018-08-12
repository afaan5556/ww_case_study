import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


######################## Part 1: Read combined data source ########################
# Read combined data
df = pd.read_csv('combined_data_source.csv')

######################## Part 2: Get data sub-sets needed for visualizations ########################

# Drop columns that are not needed for cluster collapsing
df_reduced = df.drop(['Property Name', 'Deal Id', 'NCE', 'NCE per Desk', 'NCE per USF'], axis=1)

# Function to get year filtered subset of df
def filter_year(input_df, year):
	return input_df[input_df['Open Year'] == year]

# Get separate df's for each year
df16_reduced = filter_year(df_reduced, 2016)
df17_reduced = filter_year(df_reduced, 2017)

# Function to callpse dfs by column=str
def collapse_df_cluster(input_df, column=str):
	return input_df.groupby([column]).sum()

# Collapse clusters
collapsed_df = collapse_df_cluster(df_reduced, 'Cluster')
collapsed_df16 = collapse_df_cluster(df16_reduced, 'Cluster')
collapsed_df17 = collapse_df_cluster(df17_reduced, 'Cluster')

# Calculate NCE, NCE per Desk, and NCE per USF
for i in [collapsed_df16, collapsed_df17, collapsed_df]:
	i['NCE'] = i['Capital Expenditure'] - i['TI Monies Received']
	i['NCE per Desk'] = i['NCE'] / i['Desk Count']
	i['NCE per USF'] = i['NCE'] / i['USF']

# Set up a dictionary to hold keys (cluster) and values (cluster filtered df collapsed by market)
cluster_dict ={}
for i in df_reduced['Cluster'].unique():
	cluster_dict[str(i)] = df_reduced[df_reduced['Cluster'] == i].sort_values(by='Market').set_index(['Market', 'Project Id']).groupby(level=[0]).sum()

# Calculate NCE, NCE per Desk, and NCE per USF
for key, value in cluster_dict.items():
	value['NCE'] = value['Capital Expenditure'] - value['TI Monies Received']
	value['NCE per Desk'] = value['NCE'] / value['Desk Count']
	value['NCE per USF'] = value['NCE'] / value['USF']


######################## Part 3: Build the Visualization ########################
app = dash.Dash()

app.layout = html.Div([

######################## Part 3A: Header ########################
dcc.Markdown('''
# Case Study Submission
*An analysis of Net Capital Expenditure by market and cluster during 2016 and 2017*

*By: Afaan Naqvi*
***
#### 1. Cluster vs Year Analysis
*2016 vs 2017 cluster comparison*
'''),
######################## Part 3B: Cluster vs year analysis ########################
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

######################## Part 3C: Cluster vs cluster analysis ########################
dcc.Markdown('''
#### 2. Cluster vs Cluster Analysis
*Year agnostic cluster comparison*
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

######################## Part 3D: Market analysis ########################
dcc.Markdown('''
#### 3. Market Analysis
*Cheapest and most expensive markets to build in*
'''),
html.Div([
	html.Div([
		html.Label('Select Cluster'),
		dcc.Dropdown(
			id='cluster-input',
			options=[{'label': i, 'value': i} for i in sorted(list(cluster_dict.keys()))],
			value='Cluster 1'
			),

		],
		style={'width': '10%', 'display': 'inline-block'}),


	html.Div([

	html.Div([
		dcc.Graph(id='market-desk'),
		],
		style={'width': '48%', 'display': 'inline-block'}),

	html.Div([
		dcc.Graph(id='market-usf'),
		],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
	]),
	]),

html.Hr(),

dcc.Markdown('''
#### 4. Outlier Analysis
*Identification of properties outside the expected NCE/Desk-to-NCE/USF correlation*
'''),
######################## Part 3E: Outlier analysis ########################
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

######################## Part 4: Callbacks and functions ########################


@app.callback(
	dash.dependencies.Output('market-desk', 'figure'),
	[dash.dependencies.Input('cluster-input', 'value')])
def update_desk_graph(cluster_value):
	df = cluster_dict[cluster_value].sort_values(by='NCE per Desk', ascending=False)

	return {
	'data': [
	{'x': [i for i in df.index], 'y':[i for i in df['NCE per Desk']], 'type': 'bar', 'name': str(cluster_value)},
	],
	'layout': {
	'title': 'NCE per Desk',
	'yaxis':{
	'title': 'US$/Desk'}

	}
	}

@app.callback(
	dash.dependencies.Output('market-usf', 'figure'),
	[dash.dependencies.Input('cluster-input', 'value')])
def update_usf_graph(cluster_value):
	df = cluster_dict[cluster_value].sort_values(by='NCE per Desk', ascending=False)

	return {

	'data': [
	{'x': [i for i in df.index], 'y':[i for i in df['NCE per USF']], 'type': 'bar', 'name': str(cluster_value)},
	],
	'layout': {
	'title': 'NCE per USF',
	'yaxis':{
	'title': 'US$/USF'}

	}
	}

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
	app.run_server()