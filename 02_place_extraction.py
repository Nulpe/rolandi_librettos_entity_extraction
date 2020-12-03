import shutil
import requests
import pandas as pd
from PIL import Image
import io
import pytesseract
import os
import json
import geopy
import geonamescache
import unicodedata as ud
import string as strMod
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def isAllNum(string):
    numb=''
    for el in string:
        if el.isdigit():
            numb+=el
    if len(numb)>0:
        return int(numb)
    else: return string



def makeNumeric(element):
    if type(element) == int:
        return element
    if type(element) == list:
        return isAllNum(element[0])
    if type(element) == str:
        return isAllNum(element)


latin_letters= {}
def is_latin(uchr):
    try: return latin_letters[uchr]
    except KeyError:
         return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))

def only_roman_chars(unistr):
    return all(is_latin(uchr)
           for uchr in unistr
           if uchr.isalpha())
def notAllUpper(string):
    for el in string:
        if el.isupper():
            pass
        else: return True

def dealWithPunctuation(text):
    punc = strMod.punctuation
    punc +='’'

    string = [el if el not in punc else ' '+el+' ' for el in text]
    return  ''.join(string)

# Functions to extract entities from the text
def findYearTitle(jsonData):
    metaData = jsonData['metadata']
    title = 'no_title'
    year = 'no_year'
    for el in metaData:
        if el['label'] == 'title':
            title = el['value']
        if el['label'] == 'date_year_start':
            year = el['value']

    return title, year

def getSplitText(urlPage):
    # get text with teseract
    response = requests.get(urlPage, stream=True)
    in_memory_file = io.BytesIO(response.content)
    text = pytesseract.image_to_string(Image.open(in_memory_file))
    text = dealWithPunctuation(text)
    textSplit = text.split()
    # textSplit = [word for word in textSplit if len(word)>2]
    return textSplit

def getPotCityName(textSplit):
    pot_city_name = []
    for word in textSplit:
        for city in italianCitiesList:
            #if similar(city.lower(), word.lower())>0.9:
            if city.lower() == word.lower():
                pot_city_name.append(city.lower())
    return pot_city_name

# To compile a list of all cities
def cityDic():
    city = geonamescache.GeonamesCache().get_cities()
    citiyDic = {}
    cityList = []
    n=0
    for key in city:
        if city[key]['countrycode'] == 'IT' and city[key]['population']> 20000:
            if len(city[key]['alternatenames'][0]) != 0:
                validCityNames = [city[key]['name'].lower()] +  [name.lower() for name in city[key]['alternatenames']  if only_roman_chars(name) and notAllUpper(name) and len(name)>3]
                cityList += validCityNames
                for name in validCityNames:
                    citiyDic[name] = city[key]

            else:
                cityList+=[city[key]['name'].lower()]
                citiyDic[city[key]['name'].lower()] = city[key]

            n+=1

    cityFilter = ['regio', 'marino', 'come', 'bra', 'ramma']
    cityList = list(filter(lambda a: a not in cityFilter, cityList))
    cityList = list(set(cityList))
    print(len(cityList))
    return citiyDic, cityList



#change path according to need
inPath = '/home/nulpe/Desktop/rolandi_librettos_entity_extraction/fdh_manifests/'
outPath = '/home/nulpe/Desktop/rolandi_librettos_entity_extraction/data/'
columns =['file_name', 'title', 'date', 'coperta', 'pot_city_name', 'city_name', 'latitude', 'longitude']
df_librettos = pd.DataFrame(columns= columns)


italianCities, italianCitiesList = cityDic()





potCityMatches = 0

for idx, filename in enumerate(os.listdir(inPath)):
    tempList = []

    if filename.endswith(".json"):
        tempList.append(filename)
        with open(inPath+filename) as jsonFile:
            jsonData = json.load(jsonFile)
            title, year = findYearTitle(jsonData)
            tempList.append(title)
            tempList.append(makeNumeric(year))
            front_page = []
            pot_city_name = []

            pagesData = jsonData['sequences'][0]['canvases']
            page = 0


            #Only look at the coperte
            i=0
            coperta = True


            #get text from coperte
            while coperta:
                try:
                    el = pagesData[i]
                    i += 1

                    imageApi = el['images'][0]['resource']['service']['@id']
                    urlPage = imageApi+'/full/,512/0/default.jpg'

                    #get text with teseract & potential city name
                    textSplit = getSplitText(urlPage)
                    front_page += textSplit
                    pot_city_name = getPotCityName(textSplit)
                    coperta_appended = 0

                    if 'coperta' not in pagesData[i]['label']:
                        coperta = False
                except:
                    print('page missing')
                    break



            if len(front_page) <30:
                while len(front_page) < 100:
                    try:
                        el = pagesData[i]
                        i += 1
                        imageApi = el['images'][0]['resource']['service']['@id']
                        urlPage = imageApi + '/full/,512/0/default.jpg'

                        # get text with teseract
                        textSplit = getSplitText(urlPage)
                        front_page += textSplit
                        pot_city_name += getPotCityName(textSplit)
                        coperta_appended = 1
                    except:
                        print('page missing')
                        break






            tempList.append(front_page)
            tempList.append(pot_city_name)
            

            #Get location of first mentioned city
            if len(pot_city_name) != 0:
                tempList.append(italianCities[pot_city_name[0]]['name'])
                tempList.append(italianCities[pot_city_name[0]]['latitude'])
                tempList.append(italianCities[pot_city_name[0]]['longitude'])
            else:
                tempList.append(0)
                tempList.append(0)
                tempList.append(0)

            if len(pot_city_name) != 0:
                potCityMatches+=1


            df_librettos.loc[len(df_librettos)] =tempList

            print('we are at ', idx + 1, 'of in total', len(os.listdir(inPath)), 'librettos. We have', potCityMatches/(idx + 1)*100, '% city matches')

            if (idx+1)  % 10 == 0:
                print(df_librettos)
                df_librettos.columns = columns
                df_librettos.to_pickle(outPath+'librettos_1.pkl')
                df_librettos.to_csv(outPath+'librettos_1.csv', index=False, sep='\t', header=True)










