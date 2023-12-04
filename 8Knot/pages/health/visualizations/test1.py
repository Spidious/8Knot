import plotly.express as px
import pandas as pd

df = px.data.gapminder().query("year == 2007").query(
    "continent == 'North America'")

df.loc[df['pop'] < 2.e6, 'country'] = 'Other countries'
fig = px.pie(df, values='pop', names='country',
             title='Pop of North American continent')
