import pandas as pd
import re
import numpy as np
import spacy
from sklearn.cluster import KMeans
from tqdm import tqdm
from geopy.geocoders import Nominatim
#key = 'AIzaSyDO9Hf9LcmDIgXH_jB4pUlMcogZpYcr860'

def main(input_file, output_file):
    
    # load input file
    data = pd.read_csv(input_file, delimiter='\t', index_col='file_name')
    
    # extract place step 1
    place = r'(?i)teatro|(?i)chiesa|(?i)cappella|(?i)oratorio|(?i)theatre|(?i)casa|(?i)nozze|(?i)sala|(?i)carnevale|(?i)theatro' 
    time = r"(?i)in |(?i)anno |(?i)l'anno|(?i)il |(?i)l'autunno|(?i)la primavera|(?i)l'estate|(?i)l'inverno|(?i)dell'anno|(?i)il novembre|(?i)l'auttuno|(?i)ne' mesi di|(?i)nel mese di|(?i)per la prima opera del|(?i)per la fiera|(?i)la fiera|(?i)nel prossimo|(?i)nel |(?i)nella |(?i)nell'occasione|(?i)con l'occasione|(?i)nella stagione di|(?i)la stagione|(?i)nell'està|(?i)in occasione|(?i)per la |(?i)per il |(?i)nel presente|(?i)del \d+ |(?i)carnovale|(?i)\d+ |\, "
    
    data['location_method_1'] = [re.split(time, re.split(place,s)[1])[0].strip().strip('.') 
                                 if len(re.split(place,s)) > 1 else '' 
                                 for s in data.title]
    # some manual mapping
    data['location_method_1'] = [location.replace('moisè', 'mosè')
                                 .replace("de'", 'dei')
                                 .replace('ss.', 'santi')
                                 .replace('s.', 'san')
                                 .replace('sac.', 'sacro')
                                 .replace('gio.', 'giovanni') 
                                 for location in data['location_method_1']]
    # get location type
    data['location_type_method_1'] = [re.search(place,s).group(0)
                                      .replace('theatre', 'teatro')
                                      .replace('theatro', 'teatro') 
                                      if re.search(place,s) else '' 
                                      for s in data.title]
    
    # aggregate location name and location type
    data['location_full_method_1'] = data['location_type_method_1'] + ' ' + data['location_method_1']

    print('step 1 done')
        
    # extract place step 2
    nlp = spacy.load("it_core_news_sm")
    data['location_method_2'] = [[ent.text
                                  for ent in nlp(title).ents
                                  if ent.label_ == 'LOC']
                                  for title in data.location_full_method_1 
                                  ]
    data['location_full_method_2'] = [loc[0] if len(loc)>0 else '' 
                                      for loc in data['location_method_2']]
    
    print('step 2 done')
    
    # extract place step 3
    #geolocator = Nominatim(user_agent=key)
    #geolocate_column = data['location_full_method_2'].apply(geolocator.geocode)
    #data['location_latitude_method_2'] = geolocate_column.apply(get_latitude)
    #data['location_longitude_method_2'] = geolocate_column.apply(get_longitude)
    
    print('step 3 done')
    
    # extract place step 4
    data['location_full_method_3'] = ['Not found' if loc == '' else loc for loc in data.location_full_method_3]
    data['location_vec_method_1'] = [np.mean(np.array([token.vector for token in nlp(loc)]), axis=0) 
                                     for loc in data.location_full_method_3]
    
    kmeans = KMeans(n_clusters=150, random_state=0, max_iter=50).fit(data['location_vec_method_1'].tolist())
    data['predicted_cluster_method_1'] = data['location_vec_method_1'].apply(lambda x: kmeans.predict([x.tolist()])[0])
    
    # infer based on cluster
    cluster_theater_latitude = {}
    cluster_theater_longitude = {}
    cluster_theater = {}
    for i, cluster in enumerate(data.predicted_cluster_method_1):
        if data.location_latitude_method_3[i] != '':
            if cluster in cluster_theater_latitude.keys():
                cluster_theater_latitude[cluster].append(data.location_latitude_method_3[i])
                cluster_theater_longitude[cluster].append(data.location_longitude_method_3[i])
                cluster_theater[cluster].append(data.location_full_method_3[i])
            else:
                cluster_theater_latitude[cluster] = [data.location_latitude_method_3[i]]
                cluster_theater_longitude[cluster] = [data.location_longitude_method_3[i]]
                cluster_theater[cluster] = [data.location_full_method_3[i]]
    for k in cluster_theater_latitude.keys():
        cluster_theater_latitude[k] = max(set(cluster_theater_latitude[k]), key=cluster_theater_latitude[k].count)
    
    for k in cluster_theater_longitude.keys():
        cluster_theater_longitude[k] = max(set(cluster_theater_longitude[k]), key=cluster_theater_longitude[k].count)

    for k in cluster_theater.keys():
        cluster_theater[k] = max(set(cluster_theater[k]), key=cluster_theater[k].count)
        
    data['inferred_latitude'] = [cluster_theater_latitude[cluster] for cluster in data.predicted_cluster_method_1]
    data['inferred_longitude'] = [cluster_theater_longitude[cluster] for cluster in data.predicted_cluster_method_1]
    data['inferred_location'] = [cluster_theater[cluster] for cluster in data.predicted_cluster_method_1]
    
    print('step 4 done')

    data = data.drop(columns=['location_method_1', 'location_type_method_1', 'location_full_method_1', 'location_full_method_2', 
                              'location_method_2', 'location_full_method_3', 'location_latitude_method_3',
                              'location_longitude_method_3', 'location_vec_method_1', 'predicted_cluster_method_1'])
    print(data.sample(5))
    print('Number of rows for which no location was found:', data[data['inferred_location'] == 'Not found'].shape,
          ' over the total number of rows:', data.shape)
    
    data.to_csv(output_file, sep='\t')

    
# utils 
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
    
if __name__ == "__main__":
    input_file = 'data/librettos_theaters.csv'
    output_file = 'data/librettos_04.csv'
    main(input_file, output_file)    
