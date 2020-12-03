import pandas as pd
import re
from geopy.geocoders import Nominatim
key = 'AIzaSyDO9Hf9LcmDIgXH_jB4pUlMcogZpYcr860'
geolocator = Nominatim(user_agent=key)

locations = pd.read_csv('./data/librettos.csv', delimiter='	')
locations = pd.read_pickle('./data/librettos.pkl')

expr = r'''dramma|drama|melodramma|melodrama|melo-dramma|oratorio|favola pastorale|fauola musicale|burletta in musica|componimento sagro|azione musicale|componimento sacro|per musica|opera|tragedia|spettacolo fantastico|scena in versi|fauola tragicomica|fauola pastorale|diuertimento comico|azione romantica|farsa|commeddia|commedia|operetta|festa|cantata|intermezzo in musica|intermezzi|favola in prosa|componimento sagro|componimento|azione sacra|actio sacra|fiaba|libretto fantastico|libretto|fauola|favola|([a-rt-z])\. ''' 
locations['title_opera'] = [re.split(expr,s.lower())[0].strip().strip(',') if len(re.split(expr,s.lower())) > 0 else s for s in locations.title]

expr = r'''favola pastorale|fauola musicale|burletta in musica|componimento sagro|azione musicale|componimento sacro|spettacolo fantastico|scena in versi|fauola tragicomica|fauola pastorale|diuertimento comico|azione romantica|intermezzo in musica|intermezzi|favola in prosa|componimento sagro|componimento|azione sacra|actio sacra|libretto fantastico|opera|tragedia|farsa|commeddia|commedia|operetta|festa|cantata|dramma|drama|melodramma|melodrama|melo-dramma|oratorio|libretto|fiaba|fauola|favola'''
locations['genre_opera'] = [re.search(expr,s.lower()).group(0) if re.search(expr,s.lower()) else 'Not found' for s in locations.title]

gergo2it = {'fauola':'favola', 'drama':'dramma', 'melodrama':'melodramma', 
            'melo-dramma':'melodramma', 'actio sacra':'azione sacra', 'componimento sagro':'componimento sacro',
            'fauola pastorale':'favola pastorale', 'commeddia':'commedia', 'diuertimento comico':'divertimento comico',
            'fauola tragicomica': 'favola tragicomica'
           }
locations['genre_opera'] = locations['genre_opera'].map(lambda x: gergo2it[x] if x in gergo2it.keys() else x)

place = r'teatro|chiesa|cappella|oratorio|theatre|casa|nozze|sala|carnevale|theatro' 
time = r"in |anno |l'anno|il |l'autunno|la primavera|l'estate|l'inverno|dell'anno|il novembre|l'auttuno|ne' mesi di|nel mese di|per la prima opera del|per la fiera|la fiera|nel prossimo|nel |nella |nell'occasione|con l'occasione|nella stagione di|la stagione|nell'està|in occasione|per la |per il |nel presente|del \d+ |carnovale|\d+ |\, "
locations['location'] = [re.split(time, re.split(place,s.lower())[1])[0].strip().strip('.') if len(re.split(place,s.lower())) > 1 else 'Not found' for s in locations.title]


locations['location'] = [location.replace('moisè', 'mosè').replace("de'", 'dei').replace('ss.', 'santi').replace('s.', 'san').replace('sac.', 'sacro').replace('gio.', 'giovanni') for location in locations['location']]
locations['location_type'] = [re.search(place,s.lower()).group(0).replace('theatre', 'teatro').replace('theatro', 'teatro') if re.search(place,s.lower()) else 'Not found' for s in locations.title]
locations['location_full'] = locations['location_type'] + ' ' + locations['location']

composer = r'per musica di|maestro |posta in musica dal|musica del sig\.|musica del signor|musica è del sig\.|musica è del signor |musicata da'
locations['composer'] = [s[re.search(composer,s.lower()).span(0)[0] : re.search(composer,s.lower()).span(0)[1] + 20]  if re.search(composer,s.lower()) else 'Not found' for s in locations.title]

def get_latitude(x):
    try:
        return x.latitude
    except:
        return 'Not found'

def get_longitude(x):
    try:
        return x.longitude
    except:
        return 'Not found'

geolocate_column = locations['location_full'].apply(geolocator.geocode)
locations['location_latitude'] = geolocate_column.apply(get_latitude)
locations['location_longitude'] = geolocate_column.apply(get_longitude)

locations.to_csv('./data/librettos_1.csv')
locations.to_pickle('./data/librettos_1.pkl')
locations = pd.read_pickle('./data/librettos.pkl')
