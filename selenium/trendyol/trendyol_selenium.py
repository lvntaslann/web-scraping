from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

driver_path = "C:\\Users\\kurt_\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

liste = []

for page in range(1, 51):
    url = f"https://www.trendyol.com/sr?q=laptop&qt=laptop&st=laptop&os={page}"
    driver.get(url)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".prdct-desc-cntnr-name.hasRatings"))
        )

        names = driver.find_elements(By.CSS_SELECTOR, ".prdct-desc-cntnr-name.hasRatings")
        descs = driver.find_elements(By.CLASS_NAME, "product-desc-sub-text")
        ratings = driver.find_elements(By.CLASS_NAME, "rating-score")
        prices = driver.find_elements(By.CSS_SELECTOR, ".price-item.discounted")
        images = driver.find_elements(By.CSS_SELECTOR, ".p-card-img-wr img.p-card-img")

        if not names:
            print(f"{page}. sayfada ürün bulunamadı. Veri çekme işlemi sona erdi.")
            break

        print(f"Sayfa {page} - Ürün sayısı: {len(names)}")

        for i in range(len(names)):
            name = names[i].text.strip() if i < len(names) else "N/A"
            desc = descs[i].text.strip() if i < len(descs) else "N/A"
            rating = ratings[i].text.strip() if i < len(ratings) else "N/A"
            price = prices[i].text.strip() if i < len(prices) else "N/A"
            image = images[i].get_attribute("src") if i < len(images) else "N/A"

            liste.append([name, desc, rating, price, image])

    except Exception as e:
        print(f"{page}. sayfada hata oluştu: {str(e)}")
        continue

driver.quit()

if liste:
    df = pd.DataFrame(liste, columns=["name", "description", "rating", "price", "image"])
    print(df)
    df.to_json("trendyol_laptop.json", index=False, force_ascii=False)
else:
    print("Hiç veri çekilemedi!")
