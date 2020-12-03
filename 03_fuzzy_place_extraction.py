import pandas as pd
from difflib import SequenceMatcher
import geonamescache
import unicodedata as ud
from googletrans import Translator
translator = Translator()
from translate import Translator

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
def notAllUpper(string):
    for el in string:
        if el.isupper():
            pass
        else: return True

def makeListOutOfCsvString(csv_strings):
    list_of_strings = []
    for li in csv_strings:
        temp = ''.join([i for i in li if i.isalpha() or i == ',' ])

        temp = temp.split(',')
        if len(temp[0])==0: temp = [] #Check that there are no empty strings
        list_of_strings.append(temp)

    return list_of_strings

latin_letters= {}
def is_latin(uchr):
    try: return latin_letters[uchr]
    except KeyError:
         return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))

def only_roman_chars(unistr):
    return all(is_latin(uchr)
           for uchr in unistr
           if uchr.isalpha())


def makeFamousOperaCitiesList(city_names, long, lat):
    city_names_dic = {}
    for cityLst in city_names:
        for city in cityLst:
            if city in city_names_dic:
                city_names_dic[city] += 1
            else:
                city_names_dic[city] = 1

    popular_cities = []
    for key in city_names_dic:
        if city_names_dic[key] > 10:
            popular_cities.append(key)

    city_location_dic = {}
    for pop_cit in popular_cities:
        loc_dic = {}

        for index, cityLst in enumerate(city_names):
            if len(cityLst)>0:
                if pop_cit == cityLst[0]:
                    loc_dic['longitude'] = long[index]
                    loc_dic['latitude'] = lat[index]

        city_location_dic[pop_cit] = loc_dic



    return popular_cities, city_location_dic


def cityDicItaly():
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

def cityDic():
    city = geonamescache.GeonamesCache().get_cities()
    citiyDic = {}
    cityList = []
    n=0
    for key in city:

        if city[key]['countrycode'] in ['AT', 'DE','GB','FR'] and city[key]['population'] > 150000:
            city_name = city[key]['name']
            cityList.append(city_name.lower())
            citiyDic[city_name.lower()] = city[key]

            #it_city_name = translator.translate(city_name, dest='it').text
            translator = Translator(to_lang="it")
            it_city_name = translator.translate(city_name)

            if it_city_name != city_name:
                cityList.append(it_city_name.lower())
                citiyDic[it_city_name.lower()] = city[key]
            n+=1

    cityFilter = ['livorno',] # 'nice']
    cityList = list(filter(lambda a: a not in cityFilter, cityList))
    cityList.append('barcellona')

    print(n)
    print(len(cityList))
    print(len(cityList))
    return citiyDic, cityList


inPath = '/home/nulpe/Desktop/rolandi_librettos_entity_extraction/data/'


df_librettos = pd.read_pickle(inPath+'librettos_1.pkl')



filter_pot_city = ['casale', 'vittoria', 'desio', 'nola', 'bali', 'mira', 'sora', 'sora',
                   'genzano', 'faro']



european_dic, european_cities = cityDic()


italian_dic, italian_cities = cityDicItaly()

european_dic = {**european_dic, **italian_dic}

city_names = df_librettos.pot_city_name.tolist()

long = df_librettos.longitude.tolist()
lat = df_librettos.latitude.tolist()
popular_cities, location_pop_cities_dic = makeFamousOperaCitiesList(city_names, long, lat)



Pot_city_name_fuzzy = city_names





city_no = 0

for ind, cop in enumerate(df_librettos.coperta.tolist()):
    #print(cop)

    tempAddPotCity = []
    #Delete hand filtered cities
    for filter_city in filter_pot_city:
        if filter_city in Pot_city_name_fuzzy[ind]:
            Pot_city_name_fuzzy[ind] = [city for city in Pot_city_name_fuzzy[ind] if city !=filter_city]

    #make fuzzy matches with very popular places
    for word in cop:
        word = word.lower()
        for city in popular_cities:
            if city != word and similar(city, word) > 0.85:
                Pot_city_name_fuzzy[ind].append(city)

            elif city in word:
                Pot_city_name_fuzzy[ind].append(city)

    #Find other european cities
    for word in cop:
        word = word.lower()
        if word in european_cities:
            print(word)
            city_no+=1
            Pot_city_name_fuzzy[ind].append(word)
    if (ind+1)%50==0:
        print('we are at position', ind, 'of in total', len(df_librettos.coperta.tolist()))


print(city_no)





number_found_city = len([i for i in Pot_city_name_fuzzy if len(i)>0])
number_found_first = len([i for i in city_names if len(i)>0])

print('we have ',number_found_city ,'new cities of in total ', len(df_librettos.coperta.tolist()))
print('we have ',len(df_librettos.pot_city_name.tolist()) ,'new cities of in total ', len(df_librettos.coperta.tolist()))


print(Pot_city_name_fuzzy)
city_name = []
latitude = []
longitude = []


for pot_cities in Pot_city_name_fuzzy:
    temp_dic = {}
    for city in pot_cities:
        if city in temp_dic:
            temp_dic[city]+=1
        else:
            temp_dic[city] = 1

    if len(pot_cities)>0:
        numb_hits = temp_dic[pot_cities[0]]
        most_likely_city = pot_cities[0]
        for key in temp_dic:
            if temp_dic[key]>numb_hits:
                numb_hits=temp_dic[key]
                most_likely_city=key


        latitude.append(european_dic[most_likely_city]['latitude'])
        longitude.append(european_dic[most_likely_city]['longitude'])
        city_name.append(european_dic[most_likely_city]['name'])

    else:
        latitude.append(0)
        longitude.append(0)
        city_name.append(0)



df_librettos['pot_city_name_fuzzy'] = Pot_city_name_fuzzy
df_librettos['city_name'] = city_name
df_librettos['latitude'] = latitude
df_librettos['longitude'] = longitude





df_librettos.to_pickle(inPath+'librettos_2.pkl')
df_librettos.to_csv(inPath+'librettos_2.csv', index=False, sep='\t', header=True)
