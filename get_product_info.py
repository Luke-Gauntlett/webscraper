import re
import json
import requests
from bs4 import BeautifulSoup

def main():
    product_urls = ["https://skswholesale.co.uk/products/ea-varipump-20000","https://skswholesale.co.uk/products/aquaforte-dm-8000-70w"]
   
    all_data =[]

    for url in product_urls:
        data = scrape_product_info(url)
        all_data.append(data)

    with open("product_info.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Print the saved JSON
    print(json.dumps(all_data, ensure_ascii=False, indent=2))

def scrape_product_info(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")


    # 1) Product Name
    name_tag = soup.find('h1')
    product_name = name_tag.get_text(strip=True) if name_tag else None


    # 2) Price 
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

    stock_status_tag = soup.find('b', string=lambda t: t and "IN STOCK" in t or "OUT OF STOCK" in t)

    stock_status = stock_status_tag.get_text(strip=True) if stock_status_tag else None

    # # 4) Warranty: Look for bold text "WARRANTY:" then grab following text and any <i> element
    # warranty = None
    # warranty_bold = soup.find('b', string="WARRANTY:")
    # if warranty_bold:
    #     text_after = (warranty_bold.next_sibling or "").strip()
    #     i_tag = warranty_bold.find_next('i')
    #     if i_tag:
    #         warranty = f"{text_after} {i_tag.get_text(strip=True)}"
    #     else:
    #         warranty = text_after

    # 5) Description: Preserve HTML tags

    description_div = soup.find('div', class_='product__description')
    
    if description_div:
     
        description_html = description_div.decode_contents()
    else:
        description_html = ""

    return {
        "name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "stock_status": stock_status,
        # "warranty": warranty,
        "description_html": description_html
    }


def pence_to_pound(pence):
    if not pence:
        return None
    return f"£{pence / 100:.2f}"

if __name__ == "__main__":
    
    main()
