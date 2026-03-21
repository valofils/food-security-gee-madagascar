import pandas as pd

df = pd.read_csv("data/processed/grand_sud_monthly_ndvi_rainfall.csv")

df = df.drop(columns=["system:index", ".geo"])

df.to_csv("data/processed/grand_sud_dataset_v1.csv", index=False)

print("Clean dataset saved.")