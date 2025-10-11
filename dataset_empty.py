import pandas as pd
import json

df=pd.read_csv("queries.csv")

data=[{"query": row["query"], "json_output": []} for _, row in df.iterrows()]

with open("dataset_empty.json", "w") as f:
    json.dump(data, f, indent=2)