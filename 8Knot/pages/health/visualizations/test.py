import plotly.express as px
import pandas as pd

df = pd.DataFrame({"name": ["Luke", "Mark", "Anna", "Laura"], "number": ["5", "2", "3", "4"]})
print(df)

# graph generation
fig = px.pie(values=df['number'],
            names=df['name'])
fig.update_traces(
            textposition="inside",  
            textinfo="percent+label",
            hovertemplate="%{label} <br>Commits: %{value}<br><extra></extra>",
)

fig.show()