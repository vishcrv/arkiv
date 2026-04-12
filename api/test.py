# Open Library API Example
import requests
import pprint

# Search for a book
url = "https://openlibrary.org/search.json"
params = {"q": "revolution 2020", "limit": 1}

response = requests.get(url, params=params)
data = response.json()
pprint.pprint(data)