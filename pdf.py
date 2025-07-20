import pdfplumber
import json

data = []

with pdfplumber.open("ornek.pdf") as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            headers = table[0]
            for row in table[1:]:
                data.append(dict(zip(headers, row)))

with open("ornek.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
