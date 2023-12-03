import plotly.express as px
import pandas as pd

data = {
  "calories": [420, 380, 390, 420],
  "duration": [50, 40, 45, 50]
}

#load data into a DataFrame object:
df = pd.DataFrame(data)



# graph generation
fig = px.pie(df,
            values="calories",
            names="duration")

fig.show()