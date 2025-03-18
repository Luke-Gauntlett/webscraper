import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def get_category_urls(base_url):
    response = requests.get(base_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    category_urls = set()

    # Extract links matching '/collections/<category-name>'
    for link in soup.find_all('a', href=True):
        href = link['href']
        if re.match(r'^/collections/[a-z0-9\-]+$', href):
            full_url = urljoin(base_url, href)
            category_urls.add(full_url)

    return sorted(category_urls)


if __name__ == '__main__':
    base_url = 'https://skswholesale.co.uk/'
    categories = get_category_urls(base_url)

    
    with open("catagorie_urls.txt","w") as file:
        for catagorie in categories:
            file.write(f"{catagorie}\n")