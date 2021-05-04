# import module
import concurrent.futures
from urllib.parse import unquote

import requests
import math
import json
import re
import os
import threading
import time
import codecs
import pandas as pd
from bs4 import BeautifulSoup

# headers
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"1e6d41-cvh1ElJx+6isAG+eTJHrSw5h48M"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
}

# list to save all product
data_product = []

# page counter
index = 0


# function helper to convert image url from javascript
def get_image_url(converted_script, url):
    for key, value in converted_script.items():
        if url in key:
            try:
                previewSet = value['previewSet']
                id = previewSet['id']
            except KeyError:
                continue

            for key, value in converted_script.items():
                if id + '.previews.0' in key:
                    image_url = value['url']
                    image_url = image_url.replace('{', '').replace('}', '')

            image_url = unquote(unquote(image_url))

            return image_url


# get total page
def get_total_page(keywords):
    # parameters
    params = {
        'query': keywords,
        'ref': 'search_box'
    }

    url = 'https://www.redbubble.com/shop/'
    res = requests.get(url=url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, 'html5lib')

    # test content
    # f = open('./test.html', 'w+')
    # f.write(str(res.text))
    # f.close()

    # get result for total page
    try:
        total_result = soup.find('span', attrs={'class': 'styles__box--206r9 styles__text--NLf2i styles__body--3bpp7 styles__muted--DwP9F'}).text.strip().split()
    except:
        total_result = soup.find('span', attrs={'class':'styles__box--206r9 styles__text--NLf2i styles__body--3bpp7 styles__muted--DwP9F '}).text.strip().split()
    total_result = int(total_result[0].replace(',', ''))
    pages = math.ceil(total_result / 108)
    return pages


# function to get image_url


# getting url and dont forget add parameters page
def get_product(page, keywords):
    # parameters
    params = {
        'page': page,
        'searchType': 'find'
    }

    url = 'https://www.redbubble.com/shop/{}'.format(keywords)
    res = requests.get(url=url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, 'html5lib')
    # raise Exception(results_products_container)

    # scripts = soup.find_all('script')
    scripts = soup.find_all('script')
    selected_script = None
    for script in scripts:
        if 'window.__APOLLO_STATE__=' in str(script):
            selected_script = script
            break

    selected_script = selected_script.text
    selected_script = selected_script.replace('window.__APOLLO_STATE__=', '').replace(';', '')
    # raise Exception(selected_script)

    converted_script = json.loads(selected_script)
    # raise Exception(converted_script)
    # with open('converted_script.json','w') as outfile:
    #     json.dump(converted_script, outfile)
    print('script conterted success')

    # scrap data
    results_products_container = soup.find('div', attrs={'class': 'styles__resultsProductsContainer--3QGj9'})

    result_grid = results_products_container.find('div', attrs={'id': 'SearchResultsGrid'})
    # raise Exception(result_grid)
    products = result_grid.find_all('a', recursive=False)

    # raise Exception(products)

    # create list to save item
    list_product = []
    for product in products:
        f = open('./test.html', 'w+')
        f.write(str(product))
        f.close()

        # get item link
        item_link = product['href']
        # raise Exception(item_link)

        # get item name
        item_name_regex = re.compile('.*styles__display6--.*')
        try:
            item_name = product.find('span', attrs={'class': item_name_regex}).text
            # print(item_name)
        except:
            item_name = ''

        seller_name_regex = re.compile('.*styles__body2--*.')
        # try:
        #     seller_name = product.find('span', attrs={'class':seller_name_regex}).text
        # except :
        #     seller_name = ''

        image_url = get_image_url(converted_script=converted_script, url=item_link)
        # raise Exception(image_url)
        # get all item
        dict_data = {
            'image url': image_url,
            'item name': item_name,
            'item link': item_link
        }
        # print(dict_data)

        # save data to list
        list_product.append(dict_data)
        with open('product_list.json', 'w') as outfile:
            dict_data = {
                'list_product': list_product
            }
            json.dump(dict_data, outfile)
    print('data writed')

    return list_product


# threading for speed up
thread_local = threading.local()


# getting session
def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()

    return thread_local.session


def get_detail(product):
    global data_product
    global index
    index+=1
    session = get_session()

    # with open('./product_list.json', 'r') as product_list:
    #     product = json.load(product_list)

    url = product['item link']


    # scraping step
    print('getting detail: {}. {} of {}'.format(url, index ,len(data_product)))
    with session.get(url, headers=headers) as response:
        # error fixing

        if 'Attention Required! | Cloudflare' not in str(response.text):
            soup = BeautifulSoup(response.text, 'html5lib')
            seller = soup.find('a', attrs={'class': 'ProductConfiguration__artistLink--wueCo'})
            seller_name = seller.text
            seller_profile = seller['href']

            product['seller name'] = seller_name
            product['seller profile'] = seller_profile
            return product
        else:
            print('Blocked by CAPTCHA, please wait 30 Seconds,')
            print('Try to Fix....')
            time.sleep(30)


# all site downloads or treading
def download_all_site(data_product):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor_result = executor.map(get_detail, data_product)
        results = [result for result in executor_result]
        return results


def run():
    # input keyword
    keywords = input('Input Search Keywords: ')
    keywords = keywords.replace(' ', '+')
    global data_product

    total_pages = get_total_page(keywords)
    for page in range(total_pages):
        page += 1
        print('getting item from page: {}'.format(page))
        list_product = get_product(page, keywords)
        data_product += list_product
        print('total product saved: {}'.format(len(data_product)))

        # creating directory to save json result
    try:
        os.makedirs('results')
    except FileExistsError:
        pass

    # save result to json file
    with open('./results/{}.json'.format(keywords), 'w') as outfile:
        json.dump(data_product, outfile)

    # read data
    with open('./results/{}.json'.format(keywords), 'r') as json_file:
        data_product = json.load(json_file)

    # development
    # data_product = data_product[0:250]

    results = download_all_site(data_product)
    # raise Exception(results)

    # create excel with pandas
    print('writing excel file...')
    df = pd.DataFrame(results)
    df.to_excel('./results/{}.xlsx'.format(keywords), index=False)
    print('data generate successfully')


if __name__=='__main__':
    run()
