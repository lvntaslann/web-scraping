import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.hepsiburada.com/"
}


product_list = []
print("İşlem başladı")
for index in range(1, 50):
    url = f"https://www.hepsiburada.com/ara?q=laptop&sayfa={index}"

    try:
        session = requests.Session()
        response = session.get(url=url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            names = soup.find_all('span', class_="title-module_titleText__8FlNQ")
            prices = soup.find_all('div', class_="price-module_finalPrice__LtjvY")
            images = soup.find_all('img', class_="hbImageView-module_hbImage__Ca3xO")
            ratings = soup.find_all('span', class_="rate-module_rating__19oVu")
            
            page_product_number = 0

            for name_tag, price_tag, image_tag, rating_tag in zip(names, prices, images, ratings):
                name = name_tag.text.strip() if name_tag else "Yok"
                price = price_tag.text.strip() if price_tag else "Yok"
                image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else "Yok"
                rating = rating_tag.text.strip() if rating_tag else "Yok"

                product_list.append([name, price, image_url, rating])
                page_product_number += 1

            print(f"Sayfa {index} işlendi. Toplam ürün: {page_product_number}")
        else:
            print(f"Sayfa {index} yüklenemedi. Durum kodu: {response.status_code}")

        time.sleep(random.uniform(3, 5))

    except Exception as e:
        print(f"Sayfa {index} sırasında bir hata oluştu: {e}")

df = pd.DataFrame(product_list, columns=["Name", "Price", "Image", "Rating"])
df.to_json("hepsiburada_laptop.json", index=False, force_ascii=False)

print(f"\nToplam {len(df)} ürün başarıyla kaydedildi.")
