import requests
import json

url = "http://localhost:8000/submitData"
headers = {"Content-Type": "application/json"}

with open("request.json", "r", encoding="utf-8") as f:
    data = json.load(f)

response = requests.post(url, json=data, headers=headers)
print(response.status_code)
print(response.json())
