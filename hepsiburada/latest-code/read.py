"""
import os
import json
import glob

def fix_categories(products, folder_path):
    parent_dir = os.path.basename(os.path.dirname(folder_path))
    parent_dir = parent_dir.replace("-", " ").title()

    for product in products:
        category = product.get("category", "").lower()
        if category == "muadil":
            product["category"] = f"{parent_dir}-muadil"
        elif category in ["orijinal", "orjinal"]:
            product["category"] = f"{parent_dir}-orijinal"
    return products

def merge_all_product_files(base_dir="datav4"):
    if not os.path.exists(base_dir):
        print(f"Klasör bulunamadı: {base_dir}")
        return

    merged = []
    json_files = glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True)

    print(f"{len(json_files)} json dosyası bulundu.")

    for path in json_files:
        if "all_products" in path:
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    data = fix_categories(data, path)
                    merged.extend(data)
                else:
                    print(f"Uyarı: Liste olmayan veri atlandı → {path}")
        except Exception as e:
            print(f"Hata: {path} ({e})")

    if not merged:
        print("Hiç veri birleştirilemedi. Çıkış yapılıyor.")
        return

    output_path = os.path.join(base_dir, f"all_products_{len(merged)}.json")
    os.makedirs(base_dir, exist_ok=True)  # klasör yoksa oluştur

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Toplam {len(merged)} ürün birleştirildi → {output_path}")

# Fonksiyonu çağır
merge_all_product_files("C:/Users/kurt_/Desktop/webscraping/hepsiburada/datav4")

"""

import pandas as pd 

df = pd.read_json("C:/Users/kurt_/Desktop/webscraping/hepsiburada/datav4/all_products_2934984.json")
print(df.info())
print(df["category"].value_counts())

print(df.head())

print(df["product_url"].value_counts())