import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import time

options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
driver = uc.Chrome(options=options)

car_list = []
print("İşlem başladı")
try:
    for index in range(1, 15):
        url = f"https://www.sahibinden.com/otomobil?pagingOffset={(index - 1) * 20}"
        driver.get(url)
        time.sleep(15)
        print(f"\n[+] Sayfa {index} açıldı...")

        items = driver.find_elements(By.CSS_SELECTOR, "tr.searchResultsItem.searchResultsPromoHighlight.searchResultsPromoBold")

        print(f"[*] {len(items)} ilan bulundu.")

        for item in items:
            try:
                brand = item.find_elements(By.CSS_SELECTOR, "td.searchResultsTagAttributeValue")[0].text.strip()
                series = item.find_elements(By.CSS_SELECTOR, "td.searchResultsTagAttributeValue")[1].text.strip()
                model = item.find_elements(By.CSS_SELECTOR, "td.searchResultsTagAttributeValue")[2].text.strip()

                title = item.find_element(By.CSS_SELECTOR, "td.searchResultsTitleValue").text.strip()

                year = item.find_elements(By.CSS_SELECTOR, "td.searchResultsAttributeValue")[0].text.strip()
                km = item.find_elements(By.CSS_SELECTOR, "td.searchResultsAttributeValue")[1].text.strip()

                price = item.find_element(By.CSS_SELECTOR, "td.searchResultsPriceValue").text.strip()

                date = item.find_element(By.CSS_SELECTOR, "td.searchResultsDateValue").text.strip()

                image_td = item.find_element(By.CSS_SELECTOR, "td.searchResultsLargeThumbnail")
                img_tag = image_td.find_element(By.TAG_NAME, "img")
                img_url = img_tag.get_attribute("src") or img_tag.get_attribute("data-src")

                car_list.append([brand, series, model, title, year, km, price, date,img_url])

            except Exception as e:
                print(f"Hata oluştu: {e}")
                continue

        time.sleep(5)

finally:
    driver.quit()


df = pd.DataFrame(car_list, columns=["Brand", "Series", "Model", "Title", "Year", "KM", "Price", "Date","Image"])
df.to_json("sahibinden_araba_ilanlari.json", index=False, orient="records", force_ascii=False)
print(f"\nToplam {len(df)} ilan başarıyla kaydedildi.")
