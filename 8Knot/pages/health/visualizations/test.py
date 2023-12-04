import plotly.express as px
import pandas as pd

df = pd.DataFrame({"name": ["Luke", "Mark", "Anna", "Laura"], "number": ["5", "2", "3", "4"]})
print(df)

fig = px.bar(x=['1', '2', '3', '4'], y=['1', '2', '3', '4'])
fig.update_xaxes(rangeslider_visible=True, range=[-0.5, 15])
fig.update_layout(
    xaxis_title="Domains",
    yaxis_title="Contributions",
    bargroupgap=0.1,
    margin_b=40,
    font=dict(size=14),
)
fig.update_traces(
    hovertemplate="%{label} <br>Contributions: %{value}<br><extra></extra>",
)
fig.show()