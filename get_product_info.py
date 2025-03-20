import re
import requests
from bs4 import BeautifulSoup

def parse_table(table_soup):
    """
    Given a <table> BeautifulSoup object, parse out the first row as column headers,
    and subsequent rows as data. Return a list of row-dictionaries, e.g.:
    [
      {"HEADER1": "Value1", "HEADER2": "Value2", ...},
      ...
    ]
    """
    rows = table_soup.find_all('tr')
    if not rows:
        return []

    # First row => headings
    headers = [cell.get_text(strip=True) for cell in rows[0].find_all(['th', 'td'])]

    data_rows = []
    for row in rows[1:]:
        cells = row.find_all(['th', 'td'])
        # if the row is empty or only 1 cell, skip
        if not cells:
            continue

        # get cell text
        values = [cell.get_text(" ", strip=True) for cell in cells]
        # pad or truncate to match the number of headers
        while len(values) < len(headers):
            values.append("")
        row_dict = {}
        for i, heading in enumerate(headers):
            row_dict[heading] = values[i] if i < len(values) else ""
        data_rows.append(row_dict)

    return data_rows

def table_to_text(table_data):
    """
    Convert a list of row-dictionaries (from parse_table) into
    the requested text format:

    HEADER - value
    HEADER2 - value2
    [blank line]
    ...
    """
    lines = []
    for row_dict in table_data:
        for heading, value in row_dict.items():
            lines.append(f"{heading} - {value}")
        lines.append("")  # blank line after each row
    return "\n".join(lines)

def scrape_product_info(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1) Product name
    name_tag = soup.find('h1')
    product_name = name_tag.get_text(strip=True) if name_tag else None

    # 2) Prices (try a few possible selectors)
    #    Compare-at / regular
    #    (Some themes store the compare-at price in <s class="price-item--regular"> or .price__regular .price-item--regular, etc.)
    regular_price_tag = (
        soup.select_one('.price__regular .price-item--regular span[hidewlm]') or
        soup.select_one('s.price-item--regular span[hidewlm]') or
        soup.select_one('.price__regular .price-item--regular')
    )
    sale_price_tag = (
        soup.select_one('.price__sale .price-item--sale span[hidewlm]') or
        soup.select_one('.price__sale .price-item--sale') or
        soup.select_one('span.price-item--sale span[hidewlm]')
    )

    def get_text_or_none(tag):
        if not tag:
            return None
        return tag.get_text(strip=True)

    regular_price = get_text_or_none(regular_price_tag)
    sale_price = get_text_or_none(sale_price_tag)

    # 3) Stock status
    stock_status_tag = soup.find('b', string=lambda t: t and "IN STOCK" in t)
    stock_status = stock_status_tag.get_text(strip=True) if stock_status_tag else None

    # 4) Warranty
    warranty = None
    warranty_bold = soup.find('b', string="WARRANTY:")
    if warranty_bold:
        text_after_warranty = warranty_bold.next_sibling
        if text_after_warranty and isinstance(text_after_warranty, str):
            text_after_warranty = text_after_warranty.strip()
        else:
            text_after_warranty = ""
        i_tag = warranty_bold.find_next('i')
        if i_tag:
            warranty = f"{text_after_warranty} {i_tag.get_text(strip=True)}"
        else:
            warranty = text_after_warranty

    # 5) The main product description container
    description_div = soup.find('div', class_='product__description')
    if not description_div:
        return {
            "name": product_name,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "stock_status": stock_status,
            "warranty": warranty,
            "description_text": "",
            "dimensions_table": "",
            "technical_data_table": "",
        }

    # Copy the <div> so we can remove the <table> elements from it
    # for a plain-text version of the description
    desc_div_copy = BeautifulSoup(str(description_div), 'html.parser')

    # Find the "Dimensions" <h2> (if any) then parse its table
    dimensions_table_text = ""
    dims_header = desc_div_copy.find('h2', string=lambda t: t and "Dimensions" in t)
    if dims_header:
        dims_table = dims_header.find_next('table')
        if dims_table:
            table_data = parse_table(dims_table)
            dimensions_table_text = table_to_text(table_data)
            # remove the table from the copy so it doesn't appear in plain text
            dims_table.decompose()

    # Find the "Technical Data" <h2> (if any) then parse its table
    technical_table_text = ""
    tech_header = desc_div_copy.find('h2', string=lambda t: t and "Technical Data" in t)
    if tech_header:
        tech_table = tech_header.find_next('table')
        if tech_table:
            table_data = parse_table(tech_table)
            technical_table_text = table_to_text(table_data)
            # remove the table from the copy so it doesn't appear in plain text
            tech_table.decompose()

    # Now remove all leftover HTML tags from desc_div_copy
    # and get plain text
    # The easiest approach is get_text()
    description_text = desc_div_copy.get_text(" ", strip=True)

    return {
        "name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "stock_status": stock_status,
        "warranty": warranty,
        "description_text": description_text,
        "dimensions_table": dimensions_table_text,
        "technical_data_table": technical_table_text,
    }

if __name__ == "__main__":
    product_url = "https://skswholesale.co.uk/products/ea-varipump-20000"
    data = scrape_product_info(product_url)

    print("Name:", data["name"])
    print("Regular Price:", data["regular_price"])
    print("Sale Price:", data["sale_price"])
    print("Stock Status:", data["stock_status"])
    print("Warranty:", data["warranty"])

    print("\nDESCRIPTION (no HTML tags):")
    print(data["description_text"])

    if data["dimensions_table"]:
        print("\nDIMENSIONS TABLE:")
        print(data["dimensions_table"])

    if data["technical_data_table"]:
        print("TECHNICAL DATA TABLE:")
        print(data["technical_data_table"])
