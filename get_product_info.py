import re
import json
import requests
from bs4 import BeautifulSoup

def parse_money(pence):
    if not pence:
        return None
    return f"£{pence / 100:.2f}"

def format_table(table):
    """
    Format an HTML table into plain text.
    If a preceding h2 tag is found, its text is used as the table title.
    Each data row is output as separate lines in the form:
      Header - Cell Value
    """
    # Check for table title in previous sibling (e.g., an <h2>)
    title = ""
    prev = table.find_previous_sibling()
    if prev and prev.name == "h2":
        title = prev.get_text(strip=True)
    
    # Extract rows: use both <th> and <td>
    rows = []
    for tr in table.find_all('tr'):
        cells = [cell.get_text(separator=" ", strip=True) for cell in tr.find_all(['td', 'th'])]
        if cells:
            rows.append(cells)
    
    if not rows or len(rows) < 2:
        return ""
    
    header = rows[0]
    formatted_lines = []
    if title:
        formatted_lines.append(title)
    # Process each data row (skip header row)
    for row in rows[1:]:
        if len(row) == len(header):
            for h, cell in zip(header, row):
                formatted_lines.append(f"{h} - {cell}")
        else:
            # Fallback: join the row cells if row length doesn't match header length
            formatted_lines.append(" - ".join(row))
    return "\n".join(formatted_lines)

def scrape_product_info(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # 1) Product Name
    name_tag = soup.find('h1')
    product_name = name_tag.get_text(strip=True) if name_tag else None

    # 2) Price from embedded JSON (using script tag id "em_product_variants")
    regular_price = None
    sale_price = None
    script_tag = soup.find("script", {"id": "em_product_variants"}, type="application/json")
    if script_tag:
        try:
            variants_json = json.loads(script_tag.string)
            if variants_json and isinstance(variants_json, list):
                variant_data = variants_json[0]
                sale_price = parse_money(variant_data.get("price"))
                regular_price = parse_money(variant_data.get("compare_at_price"))
        except (json.JSONDecodeError, KeyError, IndexError, ValueError):
            pass

    # 3) Stock Status (look for a bold tag that contains "IN STOCK")
    stock_status_tag = soup.find('b', string=lambda t: t and "IN STOCK" in t)
    stock_status = stock_status_tag.get_text(strip=True) if stock_status_tag else None

    # 4) Warranty: Look for bold text "WARRANTY:" then grab following text and any <i> element
    warranty = None
    warranty_bold = soup.find('b', string="WARRANTY:")
    if warranty_bold:
        text_after = (warranty_bold.next_sibling or "").strip()
        i_tag = warranty_bold.find_next('i')
        if i_tag:
            warranty = f"{text_after} {i_tag.get_text(strip=True)}"
        else:
            warranty = text_after

    # 5) Description: Process the description div and format tables separately.
    description_div = soup.find('div', class_='product__description')
    if description_div:
        desc_copy = BeautifulSoup(str(description_div), 'html.parser')
        # Process each table found in the description
        tables = desc_copy.find_all('table')
        formatted_tables = []
        for table in tables:
            formatted_tables.append(format_table(table))
            table.decompose()  # Remove table from the copy so it doesn't duplicate
        # Get the remaining plain text (without tables)
        remaining_text = desc_copy.get_text(" ", strip=True)
        # Combine the plain text and the formatted tables (each table separated by two newlines)
        description_text = remaining_text + "\n\n" + "\n\n".join(formatted_tables)
    else:
        description_text = ""

    return {
        "name": product_name,
        "regular_price": regular_price,  # Compare-at price
        "sale_price": sale_price,        # Actual sale price
        "stock_status": stock_status,
        "warranty": warranty,
        "description_text": description_text
    }

if __name__ == "__main__":
    product_url = "https://skswholesale.co.uk/products/ea-varipump-20000"
    data = scrape_product_info(product_url)

    print("Name:", data["name"])
    print("Regular Price:", data["regular_price"])  # e.g. £280.46
    print("Sale Price:", data["sale_price"])        # e.g. £143.74
    print("Stock Status:", data["stock_status"])
    print("Warranty:", data["warranty"])
    print("\nDESCRIPTION (plain text):")
    print(data["description_text"])
