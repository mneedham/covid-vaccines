import requests
from bs4 import BeautifulSoup
import csv

response = requests.get("https://en.wikipedia.org/wiki/List_of_English_districts_by_ethnicity")

soup = BeautifulSoup(response.content)
# print(soup)

rows = soup.select("table.wikitable tbody tr")

headers = [c.text.strip() for c in rows[0].select("th")]
print(headers)

with open("data/ethnicities.csv", "w") as file:
    writer = csv.writer(file, delimiter=",")
    writer.writerow(headers)
    for row in rows[1:]:
        columns = row.select("td")
        writer.writerow([c.text.strip() for c in columns])
