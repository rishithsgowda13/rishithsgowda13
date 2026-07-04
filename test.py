import requests
import re
html = requests.get('https://github.com/users/rishithsgowda13/contributions', headers={'User-Agent': 'Mozilla/5.0'}).text
matches = re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"', html)
nonzero = 0
for m in matches:
    if int(m.group(2)) > 0:
        nonzero += 1
        print(f"Date: {m.group(1)}, Level: {m.group(2)}")
print(f"Total non-zero: {nonzero}")
