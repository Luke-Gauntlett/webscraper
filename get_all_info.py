import requests
from bs4 import BeautifulSoup
import json
import random
import string

from category_urls import category_urls

def main():
    
    product_categories = {}

    for category_url in category_urls:
        print(f"Processing {category_url}")

        split = category_url.split("/")

        category_name = split[-1].replace("-", " ").title()

        all_product_urls = []

        page = 1

        while True:
            page_url = f"{category_url}?page={page}"

            product_urls = get_product_urls(page_url)

            if not product_urls:
                break

            all_product_urls.extend(product_urls)

            page += 1

        print(f"Found {len(all_product_urls)} products in category {category_name}")
        
        for product_url in all_product_urls:

            if product_url not in product_categories:
                product_categories[product_url] = []

            if category_name not in product_categories[product_url]:
                product_categories[product_url].append(category_name)

    all_data = []

    for product_url, categories in product_categories.items():

        #print(f"Scraping {product_url}")
      
        product_variants = scrape_product_info(product_url)

        for variant in product_variants:
            variant["categories"] = categories
            variant["product_page_url"] = product_url
            variant["sku"] = generate_random_sku()
            all_data.append(variant)

    
    with open("product_info.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)





def get_product_urls(page_url):
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
   
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {page_url}: {e}")
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





def scrape_product_info(page_url):
  
    try:
        response = requests.get(page_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching product page {page_url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")

    product_name = soup.find('h1').get_text(strip=True)
    
    description_section = soup.find('div', class_='product__description')

    description_text = description_section.decode_contents() if description_section else ""
    
    stock_status_tag = soup.find('b', string=lambda t: t and ("IN STOCK" in t or "OUT OF STOCK" in t))

    page_stock_status = stock_status_tag.get_text(strip=True) if stock_status_tag else None

    variants_section = soup.find("script", {"id": "em_product_variants"}, type="application/json")

    if not variants_section:
        return [{
            "name": product_name,
            "regular_price": None,
            "sale_price": None,
            "stock_status": page_stock_status,
            "description_text": description_text
        }]

    variants_json = json.loads(variants_section.string)

    variant_products = []

    for variant_data in variants_json:
        #variant_title = variant_data.get("public_title") or variant_data.get("title") or ""
        
        variant_title = variant_data.get("title")
        
        sale_price_raw = variant_data.get("price")

        regular_price_raw = variant_data.get("compare_at_price")

        if sale_price_raw is not None:
            sale_price = pence_to_pound(sale_price_raw)
        else:
            sale_price = None

        if regular_price_raw and regular_price_raw > 0:
            regular_price = pence_to_pound(regular_price_raw)
        elif sale_price_raw is not None:
            new_regular_price = int(sale_price_raw * 1.3)
            regular_price = pence_to_pound(new_regular_price)
        else:
            regular_price = None

    
        if variant_title and variant_title.lower() != "default title" and variant_title.lower() not in product_name.lower():
            full_name = f"{product_name} - {variant_title}"
        else:
            full_name = product_name

        variant_products.append({
            "name": full_name,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "stock_status": "IN STOCK" if variant_data.get("available") else "OUT OF STOCK",
            "description_text": description_text
         })

    return variant_products







def pence_to_pound(pence):
   
    if not pence:
        return None
    return f"£{pence / 100:.2f}"





def generate_random_sku():
   
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return "SKS" + random_part




if __name__ == '__main__':
    main()
