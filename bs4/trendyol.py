import requests

url = 'https://apigw.trendyol.com/discovery-web-recogw-service/api/just-for-you/1?page=0&productStampType=TypeA&versionKey=singleProducts_JFY_Original&viewAll=true&channelId=1'

headers = {
    'User-Agent': 'Mozilla/5.0'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()

    products = data.get('result', {}).get('products', [])

    for i, urun in enumerate(products[:15], start=1):
        urun_adi = urun.get('name', 'Yok')
        marka = urun.get('brand', {}).get('name', 'Marka Yok')
        fiyat = urun.get('merchantListings', [{}])[0].get('variants', [{}])[0].get('price', {}).get('discountedPrice', 'Fiyat Yok')
        resimler = urun.get('images', [])
        ilk_resim = f"https://cdn.dsmcdn.com{resimler[0]}" if resimler else 'Resim Yok'
        rating_score = urun.get('ratingScore',{}).get('averageRating','Rating yok')

        print(f"{i}. Ürün Adı: {urun_adi}")
        print(f"   Marka: {marka}")
        print(f"   Fiyat: {fiyat} TL")
        print(f"   Resim: {ilk_resim}")
        print(f"Rating : {rating_score}")
        print("-----------")
else:
    print("Veri alınamadı. Hata kodu:", response.status_code)
