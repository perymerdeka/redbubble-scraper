import json
import re
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import unquote
import json



session = HTMLSession()

keywords = 'among us'
keywords = keywords.replace(' ', '+')


headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'accept-encoding': 'gzip, deflate, br',
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



def get_image_url(converted_script, url):
    for k, v in converted_script.items():
        if url in k:
            try:
                previewSet = v['previewSet']
                id = previewSet['id']
            except KeyError:
                continue

            for k, v in converted_script.items():
                if id+'.previews.0' in k:
                    image_url = v['url']
                    image_url = image_url.replace('{', '').replace('}', '')

            # dict_data = {
            #     'id': id,
            #     'url': url,
            #     'image_url': unquote(unquote(image_url))
            # }

            image_url = unquote(unquote(image_url))

            return image_url




def get_total_pages():
    params = {
        'page': '1',
        'searchType': 'find'
    }
    res = requests.get('https://www.redbubble.com/shop/{}'.format(keywords), headers=headers, params=params)
    # res.html.render(timeout=30)

    # f = open('res.html', 'w+')
    # f.write(res.html.html)
    # f.close()

    soup = BeautifulSoup(res.text, 'html5lib')
    product_container_regex = re.compile('.*resultsProductsContainer.*')
    results_products_container = soup.find('div', attrs={'class': 'styles__resultsProductsContainer--3QGj9'})

    next_page_available = True
    if 'Nothing matches your search for' in str(results_products_container):
        next_page_available = False

    if next_page_available:
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
        # with open('converted_script.json', 'w') as outfile:
        #     json.dump(converted_script, outfile)


        search_results = results_products_container.find('div', attrs={'id': 'SearchResultsGrid'})
        products = search_results.find_all('a', recursive=False)
        list_product_per_page = []
        for product in products:
            f = open('test.html', 'w+')
            f.write(str(product))
            f.close()

            item_link = product['href']

            # img_regex = re.compile('.*styles__productImage--.*')
            # try:
            #     img = product.find('img', attrs={'class': img_regex})
            #     img = img['src']
            # except:
            #     img = ''

            item_name_regex = re.compile('.*styles__display6--.*')
            try:
                item_name = product.find('span', attrs={'class': item_name_regex}).text
            except:
                item_name = ''

            seller_name_regex = re.compile('.*styles__body2--.*')
            try:
                seller_name = product.find('span', attrs={'class': seller_name_regex}).text
            except:
                seller_name = ''

            image_url = get_image_url(converted_script, item_link)


            dict_data = {
                'image url': image_url,
                'item name': item_name,
                'item link': item_link,
            }
            list_product_per_page.append(dict_data)
            print(dict_data)
            print('===============')

        return list_product_per_page


def get_detail(url):
    res = requests.get(url, headers=headers)
    # f = open('res.html', 'w+')
    # f.write(res.text)
    # f.close()

    soup = BeautifulSoup(res.text, 'html5lib')
    seller = soup.find('a', attrs={'class': 'ProductConfiguration__artistLink--wueCo'})
    seller_name = seller.text
    seller_profile = seller['href']

    return seller_name, seller_profile


def run():
    list_product_per_page = get_total_pages()
    for product in list_product_per_page:
        url = product['item link']

        print('getting detail: {}'.format(url))
        seller_name, seller_profile = get_detail(url)

        product['seller name'] = seller_name
        product['seller profile'] = seller_profile
        print(product)


if __name__ == '__main__':
    run()