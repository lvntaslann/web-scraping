from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

# Selenium ayarları (headless tarayıcı)
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)
driver.get("https://www.foder.com.tr/uyelerimiz/")
time.sleep(3)  # İlk yükleme için bekleme

# Sayfa sonuna kadar kaydırarak tüm içerikleri yükle
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Yeni içeriklerin yüklenmesi için bekle
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# HTML içeriğini al
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Üye bilgilerini seç
uye_tabanlar = soup.select("div#BottomBos > div.UyeTaban")
uye_listesi = []

# Her üye için bilgi topla
for uye in uye_tabanlar:
    # Görsel
    image = None
    image_tag = uye.select_one("img.img-responsive.wp-post-image")
    if image_tag:
        # Lazy-load destekli görsel kaynak kontrolü
        if image_tag.has_attr("src") and not image_tag["src"].startswith("data:image"):
            image = image_tag["src"]
        elif image_tag.has_attr("data-src"):
            image = image_tag["data-src"]
        elif image_tag.has_attr("data-lazy"):
            image = image_tag["data-lazy"]
        elif image_tag.has_attr("data-original"):
            image = image_tag["data-original"]

    # Başlık
    title_tag = uye.select_one("h3.service__heading a")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Web sitesi
    website_tag = uye.select_one("a[href^='http']")
    website = website_tag["href"] if website_tag else None

    # E-posta
    email = None
    email_tag = uye.select_one("a[href^='mailto:']")
    if email_tag:
        email = email_tag.get_text(strip=True)

    # Telefon
    phone_tag = uye.select_one("a[href^='tel:']")
    phone = phone_tag.get_text(strip=True) if phone_tag else None

    # Sonuçlara ekle
    uye_listesi.append({
        "title": title,
        "website": website,
        "email": email,
        "phone": phone,
        "image": image
    })

# JSON dosyasına yaz
with open("foder_uyeler.json", "w", encoding="utf-8") as f:
    json.dump(uye_listesi, f, ensure_ascii=False, indent=2)

# Sonuç bildirimi
print(f"{len(uye_listesi)} üye JSON dosyasına kaydedildi: foder_uyeler.json")
