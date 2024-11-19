import pandas as pd
import sqlalchemy as sq
from dash import Dash, html, dcc, callback, Output, Input, dash_table, ctx, State, dash
from flask import Flask
import plotly.graph_objects as go
import numpy as np



server = Flask("TagsTrends")

app = dash.Dash("TagsTrends", title="TagsTrends", server=server, meta_tags=[{"name": "viewport", "content": "width=device-width"}])

server = app.server

app = Dash()

# read_db = pd.read_sql(sql, create_connection()).to_csv("tags_views.csv")

tags = pd.read_csv("./tags_views.csv")


def dd_data_tags():
	df = tags
	df_tag = df.sort_values(by="created", ascending=False)
	df_tag = df_tag.loc[df_tag["created"] >= '2024-01-01']
	
	return df_tag["tags"].drop_duplicates().tolist()


def get_three_months(date_time_var):
	df = tags
	df_tag = df.sort_values(by="created", ascending=False)
	df_tag = df_tag.loc[df_tag["created"] >= '2023-12-31']
	data_list = df_tag["yearMonth"].drop_duplicates().tolist()
	
	if not date_time_var:
		data_time_index = data_list.index(data_list[0])
	else:
		data_time_index = data_list.index(date_time_var)
	
	if data_time_index == 0:
		prev_date = ""
		prev_date = df_tag["yearMonth"].drop_duplicates().tolist()[data_time_index + 1]
		next_date = df_tag["yearMonth"].drop_duplicates().tolist()[data_time_index + 2]
	else:
		prev_date = df_tag["yearMonth"].drop_duplicates().tolist()[data_time_index - 1]
		next_date = df_tag["yearMonth"].drop_duplicates().tolist()[data_time_index + 1]
	
	return [prev_date, next_date, date_time_var]


def views_scatter_year(tag):
	fig = go.Figure()
	
	df = df_year_std_dev(tag)[0]
	
	fig.add_trace(
		go.Scatter(
			name="Contest",
			x=df["created"],
			y=df["Views"],
			mode="lines",
			xaxis="x",
		
		),
	
	)
	fig.update_layout(margin=dict(l=5, r=0, t=5, b=0))
	
	return fig


def views_scatter(tag, date_time_var):
	fig = go.Figure()
	
	df = df_three_month_std_dev(tag, date_time_var)[0]
	
	upper_bound = df_three_month_std_dev(tag, date_time_var)[1]
	lower_bound = df_three_month_std_dev(tag, date_time_var)[2]
	
	fig.add_trace(
		go.Scatter(
			name="Contest",
			x=df["created"],
			y=df["Views"],
			mode="lines",
			xaxis="x",
		
		),
	
	)
	fig.update_layout(
		margin=dict(l=5, r=0, t=5, b=0),
	
	)
	
	fig.add_hline(y=upper_bound, line_width=2, annotation_text=f"{upper_bound} Upper std 'Views' bound")
	fig.add_hline(y=lower_bound, line_width=2, annotation_text=f"{lower_bound} Lower std 'Views' bound")
	
	return fig


def df_three_month_std_dev(tag, date_time_var):
	df_tag = tags.loc[tags['tags'] == tag]
	
	# df = df.loc[df["created"] > '2022-01-01']
	df_tag = df_tag.sort_values(by="created", ascending=False)
	
	filter_date_array = get_three_months(date_time_var)
	
	df = df_tag.loc[df_tag["yearMonth"].isin(filter_date_array)]
	
	mean = int(np.mean(df["Views"].tolist()))
	std_dev = np.std(df["Views"].tolist())
	
	upper_bound = int(mean + std_dev)
	lower_bound = int(mean - std_dev)
	
	return df, upper_bound, lower_bound


def df_year_std_dev(tag):
	df_tag = tags.loc[tags['tags'] == tag]
	
	df_tag = df_tag.sort_values(by="created", ascending=False)
	df_tag = df_tag.loc[df_tag["created"] >= '2024-01-01']
	
	mean = int(np.mean(df_tag["Views"].tolist()))
	std_dev = np.std(df_tag["Views"].tolist())
	
	upper_bound = int(mean + std_dev)
	lower_bound = int(mean - std_dev)
	
	return df_tag, upper_bound, lower_bound


def trend_pick_analyzer(date_time_var=None):
	trends_list = {"Tags": [], "Trend Time": []}
	
	if not date_time_var:
		return pd.DataFrame(trends_list)
	
	filter_date_array = get_three_months(date_time_var)
	
	df = tags.loc[tags["yearMonth"].isin(filter_date_array)]
	
	df = df.sort_values(by="created")
	
	items = []
	date_time = []
	
	for item in set(df["tags"].tolist()):
		filtered_df = df.loc[df["tags"] == item]
		
		headers = filtered_df.head()
		row_index = headers.index.values
		
		mean = int(np.mean(filtered_df["Views"].tolist()))
		std_dev = np.std(filtered_df["Views"].tolist())
		
		upper_bound = int(mean + std_dev)
		
		for num, index in list(zip(filtered_df["Views"].tolist(), row_index)):
			if num > upper_bound and filtered_df.loc[index]["yearMonth"] == date_time_var:
				items.append(item)
				date_time.append(filtered_df.loc[index]["created"])
	
	trends_list.update({"Tags": items, "Trend Time": date_time})
	
	trend_list_df = pd.DataFrame(data=trends_list)
	
	return trend_list_df


app.layout = html.Div(
	[
		html.H1(children='Tags trends', style={'textAlign': 'center'}),
		html.Div(id="clicked_tag"),
		html.Div(
			children=[
				
				dcc.Graph(
					id='month_scatter-tags-trends',
					figure=views_scatter("Contest", "Nov-2024"),
					style={"grid-area": "1 / 1", "height": "225px", "width": "600px"},
					config={'displayModeBar': False,
					        'scrollZoom': False
					        },
				),
				dcc.Graph(
					id='year_scatter-tags-trends',
					figure=views_scatter_year("Contest"),
					style={"grid-area": "1 / 2", "height": "225px", "width": "600px"},
					config={'displayModeBar': False,
					        'scrollZoom': False
					        },
				),
				dash_table.DataTable(
					trend_pick_analyzer().to_dict('records'),
					[{'name': i, 'id': i} for i in trend_pick_analyzer().columns],
					id="tags-trends-table",
					style_table={"grid-area": "1 / 3", "align-items": "end"}
				)
			],
			style={"display": "grid", "grid-template-rows": "1fr", "grid-template-columns": "1fr 1fr 0.5fr"}
		),
		html.Div(
			children=[
				dcc.Dropdown(
					id="dd-tags",
					value="Contest",
					options=dd_data_tags(),
					style={"grid-area": "1 / 1", "width": "300px"}
				),
				dcc.Dropdown(
					id="dd-time",
					value="Nov-2024",
					style={"grid-area": "1 / 2", "width": "150px"}
				),
			],
			style={"display": "grid", "grid-template-rows": "1fr", "grid-template-columns": "0.5 0.5fr",
			       "width": "500px"}
		)
	]
)


@callback(
	[Output('month_scatter-tags-trends', 'figure'),
	 Output('year_scatter-tags-trends', 'figure'),
	 Output("tags-trends-table", "selected_cells"),
	 Output("tags-trends-table", "active_cell"),
	 Output("clicked_tag", "children")],
	State("dd-time", "value"),
	[Input('dd-tags', 'value'),
	 Input('tags-trends-table', 'active_cell')]
)
def update_graph(date_time, tag, active_cell):
	value = tag
	if active_cell:
		clicked_cell = active_cell["row"]
		value = trend_pick_analyzer(date_time).to_dict('records')[clicked_cell]["Tags"]
	
	return views_scatter(value, date_time), views_scatter_year(value), [], None, [value]


@callback(
	Output("tags-trends-table", "data"),
	Input("dd-time", "value")
)
def table_update(value):
	return trend_pick_analyzer(value).to_dict('records')


@callback(
	Output("dd-time", "options"),
	Input("dd-time", "value")
)
def dd_time_updater(value):
	df = tags
	df = df.loc[df["created"] > '2020-01-01']
	df = df.sort_values(by="created", ascending=False)
	
	return df["yearMonth"].drop_duplicates().tolist()


if __name__ == '__main__':
	app.run(debug=False, host="0.0.0.0", port=1701)
	
	