import codecs
import glob
import json
import os
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

import gspread



# base_url
base_url = 'https://www.yell.com'
# keyword
keywords = 'Hotel'
location = 'London'



headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36'
}


def get_total_pages():
    params = {
        'keywords': keywords,
        'location': location,
        'scrambleSeed': '1189397696',
    }

    url = 'https://www.yell.com/ucs/UcsSearchAction.do?'
    req = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    pagination = soup.find('div', attrs={'class': 'row pagination'}).findAll('a', attrs={'class': 'btn'})
    total = len(pagination)
    return total


def get_url_per_page(page):
    data_links = []
    params = {
        'keywords': keywords,
        'location': location,
        'pageNum': page

    }
    url = 'https://www.yell.com/ucs/UcsSearchAction.do?'
    req = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    product_Link = soup.findAll('div', attrs={'class': 'row businessCapsule--mainRow'})

    for item in product_Link:
        link = item.find('div', attrs={'class': 'businessCapsule--titSpons'}).find('a')['href']
        data_links.append(link)
    # print(len(data_links))
    return data_links
    # data_url = {
    #     'url_list':data_links
    # }
    # with open('results.json', 'w') as outfile:
    #     json.dump(data_url, outfile)

# counter
counter = 0

def get_detail(url):
    global counter, address, city, postal_code
    req = requests.get(base_url + url, headers=headers)
    f = open('./tes.html', 'w+')
    f.write(req.text)

    # read file tes.html for error handling
    reader = codecs.open('./tes.html', 'r').read()
    parser = BeautifulSoup(reader, 'html.parser')
    title_text = parser.find('title').text.strip()
    # print(title_text)
    while 'Are you human?' in title_text:
        with open('server_list_label_only.txt', 'r') as data_server:
            vpn_list = data_server.readlines()
            server_list = []
            for item in vpn_list:
                server_list.append(item.strip())

            # try blocks
            try:
                print('Try VPN Server ... {}'.format(server_list[counter]))
                os.system('windscribe connect {}'.format(server_list[counter]))
                counter +=1
                break
            except UnboundLocalError:
                continue

    print('Getting Detail: {}'.format(url))
    req = requests.get(base_url + url, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    try:
        title = soup.find('h1', attrs={'class': 'text-h1 businessCard--businessName'}).text.strip()
    except:
        title = soup.find('div', attrs={'class': 'text-h1 businessCard--businessName'})

    more_info = soup.findAll('span', attrs={'class': 'address'})
    for info in more_info:
        address = info.find('span', attrs={'itemprop': 'streetAddress'}).text.strip()
        city = info.find('span', attrs={'itemprop': 'addressLocality'}).text.strip()
        postal_code = info.find('span', attrs={'itemprop': 'postalCode'}).text.strip()

    try:
        website = soup.find('a', attrs={'class': 'btn btn-big btn-yellow businessCard--callToAction'})['href']
        telp = soup.find('span', attrs={'class': 'business--telephoneNumber'}).text.strip()
    except:
        website = 'No Website'
        telp = 'No Telephone'

    data_detail = {
        'title': title,
        'address': address,
        'city': city,
        'postal Code': postal_code,
        'telp': telp,
        'website': website
    }

    return data_detail

    # except requests.RequestException as e:
    # print(e)


def main():
    # counter = 0
    count = 'y'
    while count == 'y':
        print('++' * 10, 'Scraping Yell.com', '++' * 10)
        print('==' * 10, ' MAIN MENU ', '==' * 10)
        print()
        print('1. Getting All URL ')
        print('2. Geting Detail per URL ')
        print('3. Generate Result To CSV File on local')
        print('4. Generate Csv and import to GDrive')
        print('5. Exit From Program')


        get_input = int(input("Input Your Choice: "))

        if get_input == 1:
            total_pages = get_total_pages()

            links = []
            for page in range(total_pages):
                page += 1
                url_per_page = get_url_per_page(page)
                links += url_per_page
            print('Total Page is', page)

            results = []
            for url in links:
                results.append(url)
            print('{} URL Founds'.format(len(results)))
            data_url = {
                'url_list': results
            }
                #     writing to Json File
            with open('urls.json', 'w') as url_json:
                json.dump(data_url, url_json)
            print('Generating URL Complete check file urls.json')
            count = 'n'

        elif get_input == 2:
            # counter = 0
            start = int(input('Start From: '))
            endlist = int(input('Endlist Value: '))

            total = get_total_pages()
            for page in range(total):
                page += 1

            with open('urls.json') as read_json:
                data = json.load(read_json)

            urls = data['url_list']
            urls = urls[start:endlist]

            for id, url in enumerate(urls):
                time.sleep(1)
                print()
                print('Generated Json File: {} of {}'.format(start + id + 1, endlist))
                data_dict = get_detail(url)

                with open('downloads/{}.json'.format(start + id + 1), 'w') as files:
                    json.dump(data_dict, files)
                print('Generated Json Complete Check downloads directory')


        elif get_input == 3:
            files = sorted(glob.glob('./downloads/*.json'), key=lambda x: float(re.findall("(\d)", x)[0]))
            all_datas = []
            for file in files:
                print('Generating File Json: ', file)
                with open(file) as json_file:
                     datas = json.load(json_file)
                all_datas.append(datas)
                #         write to CSV with pandas
            df = pd.DataFrame(all_datas)
            df.to_csv('DataList.csv')
            print()
            print('Data Generated To Csv')

        elif get_input == 4:
            # get sheets from API and
            gc = gspread.service_account(filename='yelldev-key.json')
            sheets = gc.open_by_key('1e87M6GfKmQCALI-IcmV6pYgy7aiszov4JZf_0CjR0DQ')
            # read worksheet on drive
            worksheet = sheets.sheet1 # why sheet1 because in this case we only have one sheet
            scrap_res = sorted(glob.glob('./downloads/*.json'), key=lambda x: float(re.findall("(\d)", x)[0]))
            scrap_datas = []
            for scrap in scrap_res:
                print('generating JSON: ', scrap)
                with open(scrap) as json_file:
                    datas = json.load(json_file)
                scrap_datas.append(datas)
            df = pd.DataFrame(scrap_datas)
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            print('Upload Complete')



        elif get_input == 5:
            count = 'n'
            print('Program Exited')


if __name__ == '__main__':
    main()
