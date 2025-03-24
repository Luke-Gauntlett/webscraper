import requests
from bs4 import BeautifulSoup
import json
import random
import string

# Import the list of category URLs from your module.
from category_urls import category_urls

def extract_category_name(url):
 
    parts = url.split("/collections/")
    if len(parts) > 1:
        category = parts[1].split("?")[0]
        return category.replace("-", " ").title()
    return url

def get_all_product_urls(category_url):
    """
    Retrieve all product URLs from a given category page, handling pagination.
    """
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
    """
    Scrape product URLs from a given category page URL.
    """
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

def scrape_product_info(url):
    """
    Scrape product details (name, price, stock status, and description) from a product page.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching product page {url}: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 1) Product Name
    name_tag = soup.find('h1')
    product_name = name_tag.get_text(strip=True) if name_tag else None

    # 2) Price (regular and sale)
    regular_price = None
    sale_price = None
    script_tag = soup.find("script", {"id": "em_product_variants"}, type="application/json")
    if script_tag:
        try:
            variants_json = json.loads(script_tag.string)
            if variants_json and isinstance(variants_json, list):
                variant_data = variants_json[0]
                sale_price = pence_to_pound(variant_data.get("price"))
                regular_price = pence_to_pound(variant_data.get("compare_at_price"))
        except (json.JSONDecodeError, KeyError, IndexError, ValueError):
            pass

    # 3) Stock Status
    stock_status_tag = soup.find('b', string=lambda t: t and ("IN STOCK" in t or "OUT OF STOCK" in t))
    stock_status = stock_status_tag.get_text(strip=True) if stock_status_tag else None

    # 4) Description (with HTML formatting preserved)
    description_div = soup.find('div', class_='product__description')
    description_html = description_div.decode_contents() if description_div else ""

    return {
        "name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "stock_status": stock_status,
        "description_html": description_html
    }

def pence_to_pound(pence):
    """
    Convert a price from pence to a formatted pound string.
    """
    if not pence:
        return None
    return f"£{pence / 100:.2f}"

def generate_random_sku():
    """
    Generate a random SKU starting with 'SKS' followed by 10 alphanumeric characters.
    """
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return "SKS" + random_part

def main():
    # Dictionary mapping product URLs to a list of category names in which they appear.
    product_categories = {}

    # Loop through each category URL from the imported list.
    for category_url in category_urls:
        print(f"Processing category: {category_url}")
        category_name = extract_category_name(category_url)
        product_urls = get_all_product_urls(category_url)
        print(f"Found {len(product_urls)} products in category '{category_name}'")
        for product_url in product_urls:
            if product_url not in product_categories:
                product_categories[product_url] = []
            if category_name not in product_categories[product_url]:
                product_categories[product_url].append(category_name)

    all_data = []
    # For each unique product URL, scrape its details and add extra fields.
    for product_url, categories in product_categories.items():
        print(f"Scraping product: {product_url}")
        product_info = scrape_product_info(product_url)
        if not product_info:
            continue
        product_info["categories"] = categories
        product_info["product_url"] = product_url
        product_info["sku"] = generate_random_sku()
        all_data.append(product_info)

    # Write the collected product data to a JSON file.
    with open("product_info.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Optionally, print the JSON data.
    print(json.dumps(all_data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
