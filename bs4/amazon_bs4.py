import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

product_list = []

for index in range(1, 50):
    url = f"https://www.amazon.com.tr/s?k=laptop&page={index}"
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            products = soup.select('div.puis-card-container.s-card-container.puis-card-border')

            page_product_number = 0

            for product in products:
                name_tag = product.find('h2', class_="a-size-base-plus a-spacing-none a-color-base a-text-normal")
                name = name_tag.text.strip() if name_tag else "Yok"

                price_whole = product.find('span', class_="a-price-whole")
                price_fraction = product.find('span', class_="a-price-fraction")
                if price_whole and price_fraction:
                    price = price_whole.text.strip() + price_fraction.text.strip()
                elif price_whole:
                    price = price_whole.text.strip()
                else:
                    price = "Yok"

                image_tag = product.find('img', class_="s-image")
                image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else "Yok"

                rating_tag = product.find('span', class_="a-icon-alt")
                if rating_tag:
                    rating_raw = rating_tag.text.strip()
                    if "üzerinden" in rating_raw:
                        rating_value = rating_raw.split("üzerinden")[1].strip().split()[0]
                    else:
                        rating_value = rating_raw
                    rating_value = rating_value.replace(",", ".")
                else:
                    rating_value = "0"

                product_list.append([name, price, image_url, rating_value])
                page_product_number += 1

            print(f"Sayfa {index} işlendi. Toplam ürün: {page_product_number}")

        else:
            print(f"Sayfa {index} yüklenemedi. Durum kodu: {response.status_code}")

        time.sleep(1.5)

    except Exception as e:
        print(f"Sayfa {index} sırasında bir hata oluştu: {e}")

df = pd.DataFrame(product_list, columns=["Name", "Price", "Image", "Rating"])
df.to_json("amazon_laptop.json", index=False, force_ascii=False)

print(f"\nToplam {len(df)} ürün başarıyla kaydedildi.")
