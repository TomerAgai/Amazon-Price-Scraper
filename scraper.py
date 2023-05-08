import re
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from forex_python.converter import CurrencyRates


# Define the Amazon websites to scrape
AMAZON_SITES = {
    "com": "https://www.amazon.com",
    "co.uk": "https://www.amazon.co.uk",
    "de": "https://www.amazon.de",
    "ca": "https://www.amazon.ca"
}


def build_amazon_search_url(query, site, asin=None):
    base_url = AMAZON_SITES[site]
    if asin:
        search_url = f"{base_url}/dp/{asin}"
    else:
        search_url = f"{base_url}/s?{urllib.parse.urlencode({'k': query})}&ref=nb_sb_noss"
    return search_url


USER_AGENTS = [  # Use a list of User-Agents and rotate them between requests.
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
]


def get_request_headers():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    return headers


def search_amazon(query, site, asin=None, product_price=False):
    url = build_amazon_search_url(query, site, asin)
    headers = get_request_headers()
    time.sleep(3)  # Add a 3-second delay
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    if asin:
        # If ASIN is provided, only look for the product details in the current page
        items = [soup]
    else:
        items = soup.select(".s-result-item")

    results = []
    for item in items:
        if product_price:
            name = soup.select_one("#productTitle")
            image = soup.select_one("#landingImage")
            price = soup.select_one(
                "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen, .a-color-price")
            link = url
            rating = soup.select_one("#acrPopover")

            if name:
                name = name.text.strip()
            if image:
                image = image["src"]
            if price:
                price = price.text.strip()
            if rating:
                rating_text = rating["title"]
                rating_value = re.search(r"(\d+(\.\d+)?)", rating_text)
                if rating_value:
                    rating = float(rating_value.group(1))
                else:
                    rating = None
        else:
            asin = item.get("data-asin")
            if not asin:

                continue
            name = item.select_one(
                "h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-4, h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2")
            if name:
                name = name.text.strip()
            else:

                continue

            image = item.select_one(".s-image")
            if image:
                image = image["src"]
            else:
                continue

            price = item.select_one(".a-price .a-offscreen")
            if price:
                price = price.text.strip()
            else:
                continue

            link = item.select_one(".a-link-normal.a-text-normal")
            if link:
                link = link["href"]
                if not link.startswith("http"):
                    link = "https://www.amazon.com" + link
            else:
                continue

            rating = item.select_one(
                ".a-icon.a-icon-star-small span.a-icon-alt")
            if rating:
                rating_text = rating.text
                rating_value = re.search(r"(\d+(\.\d+)?)", rating_text)
                if rating_value:
                    rating = float(rating_value.group(1))
                else:
                    rating = None
            else:
                rating = None

        result = {
            "site": site,
            "name": name,
            "image": image,
            "price": price,
            "link": link,
            "rating": rating,
            "asin": asin
        }
        results.append(result)
        if len(results) >= 10:
            break
    return results


def extract_asin_from_url(url):
    match = re.search(r"/dp/(\w+)/", url)
    if match:
        return match.group(1)
    return None


def get_prices_for_asin(asin):
    prices_data = {}

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(
            get_prices_for_site, site, asin): site for site in AMAZON_SITES.keys()}
        for future in as_completed(futures):
            site = futures[future]
            try:
                result = future.result()
                if result:
                    prices_data[result[0]] = result[1]
            except Exception as exc:
                print(f"{site} generated an exception: {exc}")

    return prices_data


def get_prices_for_site(site, asin):
    results = search_amazon("", site, asin, product_price=True)
    if results:
        result = results[0]
        converted_price = convert_price_to_usd(result["price"], site)
        return site, {
            "price": converted_price,
            "link": result["link"],
            "name": result["name"],
            "rating": result["rating"]
        }
    return site, None


def convert_price_to_usd(price_str, site):
    if price_str is None:
        return None
    currency_conversion = {
        "com": 1,
        "co.uk": 1.3,  # GBP to USD
        "de": 1.1,  # EUR to USD
        "ca": 0.8  # CAD to USD
    }

    price = re.findall(r"\d+\.\d+", price_str)
    if price:
        converted_price = float(price[0]) * currency_conversion[site]
        return f"${converted_price:.2f}"
    return price_str
