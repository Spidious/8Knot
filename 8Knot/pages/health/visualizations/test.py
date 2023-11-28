import plotly.express as px

# graph generation
fig = px.pie(values=[8, 8, 8, 8, 8],
            names=["eight", "eight", "eight", "eight", "eight"])
fig.update_traces(
            textposition="inside",  
            textinfo="percent+label",
            hovertemplate="%{label} <br>Commits: %{value}<br><extra></extra>",
)

fig.show()