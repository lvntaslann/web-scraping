from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

driver_path = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

product_list = []
print("İşlem başladı")

for page in range(1, 50):
    url = f"https://www.hepsiburada.com/ara?q=laptop&sayfa={page}"
    driver.get(url)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "productCard-module_productCardRoot__Yf7qs"))
        )
        
        cards = driver.find_elements(By.CLASS_NAME, "productCard-module_productCardRoot__Yf7qs")
        if not cards:
            print(f"{page}. sayfada ürün bulunamadı. Veri çekme işlemi sona erdi.")
            break
        
        print(f"Sayfa {page} - Ürün kartı sayısı: {len(cards)}")

        for card in cards:
            try:
                name = card.find_element(By.CLASS_NAME, "title-module_titleText__8FlNQ").text.strip()
            except:
                name = "N/A"
            try:
                price = card.find_element(By.CLASS_NAME, "price-module_finalPrice__LtjvY").text.strip()
            except:
                price = "N/A"
            try:
                image = card.find_element(By.CLASS_NAME, "hbImageView-module_hbImage__Ca3xO").get_attribute("src")
            except:
                image = "N/A"
            try:
                rating = card.find_element(By.CLASS_NAME, "rate-module_rating__19oVu").text.strip()
            except:
                rating = "N/A"
            
            product_list.append([name, price, image, rating])
            
    except Exception as e:
        print(f"{page}. sayfada hata oluştu: {e}")
        break

driver.quit()

if product_list:
    df = pd.DataFrame(product_list, columns=["name", "price", "image", "rating"])
    print(df.head())
    df.to_json("hepsiburada_laptop.json", index=False, force_ascii=False)
    print(f"\nToplam {len(df)} ürün başarıyla kaydedildi.")
else:
    print("Hiç veri çekilemedi!")
