import requests
from bs4 import BeautifulSoup

category_urls = [
    "https://skswholesale.co.uk/collections/pond-pumps",
    "https://skswholesale.co.uk/collections/variable-flow-pumps",
    "https://skswholesale.co.uk/collections/submersible-pumps"]



def main():
    with open("product_urls.txt", "w", encoding="utf-8") as file:
        for url in category_urls:
            product_urls = get_all_product_urls(url)

            for url in product_urls:
                file.write(url + "\n")

            file.write("\n")





def get_all_product_urls(category_url):

    all_urls = []

    page = 1

    while True:

        paged_url = f"{category_url}?page={page}"
    
        page_urls = get_product_urls(paged_url)

        if not page_urls:
            break

        all_urls.extend(page_urls)

        page += 1

    return all_urls





def get_product_urls(url):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')

    product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
    
    product_urls = []

    for link in product_links:
        href = link.get('href')
       
        if href.startswith('/'):
            href = "https://skswholesale.co.uk" + href

        if href not in product_urls:  
            product_urls.append(href)

    return product_urls

if __name__ == '__main__':
    main()
