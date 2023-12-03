import plotly.express as px
import pandas as pd

df = pd.DataFrame({"name": ["Luke", "Mark", "Anna", "Laura", "Lydia", "Grant", "Lisa", "Ted"], "number": ["5", "2", "3", "4", "1", "6", "7", "8"]})

new = df['name'].tolist()
df['new'] = (df['name'].tolist())[:int(len(df['name'].tolist())/3)]

pass
