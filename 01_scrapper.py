import os
import time
import requests as r
from bs4 import BeautifulSoup

MAIN_COLLECTION_URL = 'http://dl.cini.it/collections/show/1358'
PREFIX_STR_MANIFEST = 'http://dl.cini.it/oa/collections/{}/manifest.json'

main_collection_page = r.get(MAIN_COLLECTION_URL)
print(main_collection_page.status_code)

soup = BeautifulSoup(main_collection_page.text, 'html.parser')
soup_sub = soup.find(
    "ul", {"id": "collection-subtree-ul"}).find(
        "div", {"id": "collection-tree"}).find(
            "div", {"id": "collection-tree"}).find(
                "ul", {"id": "collection-subtree-ul"})

## print(soup_sub.prettify())

all_manifest_urls = [
    PREFIX_STR_MANIFEST.format(li.a.get('href').split('/')[-1]) for li in soup_sub]

data_dir_exists = 'fdh_data' in os.listdir(os.getcwd())

## Please delete dir if you have the same one
if not data_dir_exists:
    os.makedirs('./fdh_data')

for i, u in enumerate(all_manifest_urls):
    response = r.get(u)
    time.sleep(2) ## for delay and no DDOS
    if response.status_code != 200:
        print('Manifest not found for: {}'.format(u))
    else:
        with open('fdh_data/data_{}.json'.format(i), 'w') as f:
            json.dump(response.json(), f)
