import pandas as pd
df = pd.read_json("datav3/all_products_143272.json")
print(df["supercategory"].unique())

print(df.info())
print(df.head())
print(df["category"].value_counts())
print(df[df["supercategory"]=="Bilinmeyen"].head(10))
print(df["supercategory"].value_counts())
