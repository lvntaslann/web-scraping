import cloudscraper
from bs4 import BeautifulSoup
import time
import pandas as pd

baseurl = "https://www.thewhiskyexchange.com"
scraper = cloudscraper.create_scraper()

productslinks = []
whisky = []
print("İşlem başladı...")

for x in range(1, 6):
    time.sleep(3)
    url = f'{baseurl}/c/35/japanese-whisky?pg={x}'
    response = scraper.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    products = soup.find_all('li', class_='product-grid__item')
    for item in products:
        for link in item.find_all('a', href=True):
            productslinks.append(f"{baseurl}/{link['href']}")

print(f"Toplam {len(productslinks)} ürün linki bulundu.\n")

print(productslinks)
for link in productslinks:
    time.sleep(3)
    r = scraper.get(link)
    soups = BeautifulSoup(r.content, 'lxml')

    try:
        name = soups.find('h1', class_='product-main__name').text.strip()
    except:
        name = 'no-name'

    try:
        price = soups.find('p', class_='product-action__price').text.strip()
    except:
        price = 'no-price'

    try:
        rating = soups.find('div', class_='product-main__attraction').text.strip()
    except:
        rating = 'no-rating'

    whisky.append({
        'name': name,
        'rating': rating,
        'price': price
    })

if whisky:
    df = pd.DataFrame(whisky)
    print(df.head())
    df.info()
    df.to_csv('whisky.csv', index=False, encoding='utf-8-sig')
    print("\n İşlem bitti, 'whisky.csv' dosyasına kaydedildi.")
else:
    print("\n Hiç ürün bulunmadı. Lütfen site yapısını kontrol edin.")
