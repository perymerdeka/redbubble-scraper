import concurrent.futures
import json
import os
import re
import requests
import threading
import pandas as pd

from bs4 import BeautifulSoup
from urllib.parse import unquote

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9,id;q=0.8',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"1d827e-rli6+LKFcaBH4Irc53XZHOqY+nQ"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.30 Safari/537.36'
}

all_products = []
index = 0


def get_image_url(converted_script, url):
    for k, v in converted_script.items():
        if url in k:
            try:
                previewSet = v['previewSet']
                id = previewSet['id']
            except KeyError:
                continue

            for k, v in converted_script.items():
                if id + '.previews.0' in k:
                    image_url = v['url']
                    image_url = image_url.replace('{', '').replace('}', '')

            image_url = unquote(unquote(image_url))

            return image_url


def get_product_per_page(page, keywords):
    params = {
        'page': page,
        'searchType': 'find'
    }
    res = requests.get('https://www.redbubble.com/shop/{}'.format(keywords), headers=headers, params=params)

    soup = BeautifulSoup(res.text, 'html5lib')
    results_products_container = soup.find('div', attrs={'class': 'styles__resultsProductsContainer--3QGj9'})

    next_page_available = True
    if 'Nothing matches your search for' in str(results_products_container) or 'We found a person that matched' in str(
            results_products_container):
        next_page_available = False

    list_product_per_page = []
    if next_page_available:
        scripts = soup.find_all('script')
        selected_script = None
        for script in scripts:
            if 'window.__APOLLO_STATE__=' in str(script):
                selected_script = script
                break

        selected_script = selected_script.text
        selected_script = selected_script.replace('window.__APOLLO_STATE__=', '').replace(';', '')

        converted_script = json.loads(selected_script)
        # with open('converted_script.json', 'w') as outfile:
        #     json.dump(converted_script, outfile)

        search_results = results_products_container.find('div', attrs={'id': 'SearchResultsGrid'})
        products = search_results.find_all('a', recursive=False)

        for product in products:
            item_link = product['href']

            item_name_regex = re.compile('.*styles__display6--.*')
            try:
                item_name = product.find('span', attrs={'class': item_name_regex}).text
            except:
                item_name = ''

            image_url = get_image_url(converted_script, item_link)

            dict_data = {
                'image url': image_url,
                'item name': item_name,
                'item link': item_link,
            }
            list_product_per_page.append(dict_data)

    return list_product_per_page


thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def download_site(product):
    global all_products
    global index
    index += 1
    session = get_session()
    url = product['item link']

    print('getting detail: {}. {} of {}'.format(url, index, len(all_products)))
    with session.get(url, headers=headers) as response:
        soup = BeautifulSoup(response.text, 'html.parser')
        seller = soup.find('a', attrs={'class': 'ProductConfiguration__artistLink--wueCo'})
        seller_name = seller.text
        seller_profile = seller['href']

        product['seller name'] = seller_name
        product['seller profile'] = seller_profile

        return product


def download_all_sites(all_products):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor_result = executor.map(download_site, all_products)
        results = [result for result in executor_result]
        return results


def run():
    keywords = input('Input keywords for search: ')
    keywords = keywords.replace(' ', '+')
    global all_products

    page = 0
    while True:
        page += 1
        print('Getting links for page: {}'.format(page))
        list_product_per_page = get_product_per_page(page, keywords)
        all_products += list_product_per_page
        print('Total product link saved: {}'.format(len(all_products)))
        if list_product_per_page == []:
            break

    try:
        os.makedirs('results')
    except FileExistsError:
        pass

    with open('./results/{}.json'.format(keywords), 'w') as outfile:
        json.dump(all_products, outfile)

    with open('./results/{}.json'.format(keywords)) as json_file:
        all_products = json.load(json_file)

    # Dev mode
    # all_products = all_products[0:10]

    results = download_all_sites(all_products)

    print('Creating excel.....')
    df = pd.DataFrame(results)
    df.to_excel('./results/{}.xlsx'.format(keywords), index=False)


if __name__ == '__main__':
    run()
