import requests

# set the search query
query = "coffee"

# set the URL of the search result page
url = f"https://www.google.com/search?q={query}"

# set headers to imitate a web browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}

# send a GET request and get the response
response = requests.get(url, headers=headers)

# extract the HTML content from the response
html_content = response.content

# print(html_content)
