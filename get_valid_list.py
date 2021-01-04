import urllib.request
with urllib.request.urlopen('https://raw.githubusercontent.com/cristianritter/licenses/main/codes') as f:
    html = f.read().decode('utf-8')

print(html)