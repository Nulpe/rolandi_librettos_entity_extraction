import pandas as pd
import re
import numpy as np
import spacy
from sklearn.cluster import KMeans
from tqdm import tqdm

def main(input_file, output_file):
    
    # load input file
    data = pd.read_csv(input_file, delimiter='\t', index_col='file_name')
    
    # extract genre step 1
    genre = r'''favola pastorale|fauola musicale|burletta in musica|componimento sagro|azione musicale|componimento sacro|spettacolo fantastico|scena in versi|fauola tragicomica|fauola pastorale|diuertimento comico|azione romantica|intermezzo in musica|intermezzi|favola in prosa|componimento sagro|componimento|azione sacra|actio sacra|libretto fantastico|opera|tragedia|farsa|commeddia|commedia|operetta|festa|cantata|dramma|drama|melodramma|melodrama|melo-dramma|oratorio|libretto|fiaba|fauola|favola'''
    data['genre_opera'] = [re.search(genre,s.lower()).group(0) if re.search(genre,s.lower()) 
                           else 'Not found' for s in data.title]
    
    # some manual mapping
    gergo2it = {'fauola':'favola', 'drama':'dramma', 'melodrama':'melodramma', 
                'melo-dramma':'melodramma', 'actio sacra':'azione sacra', 'componimento sagro':'componimento sacro',
                'fauola pastorale':'favola pastorale', 'commeddia':'commedia', 'diuertimento comico':'divertimento comico',
                'fauola tragicomica': 'favola tragicomica'
               }
    data['genre_opera'] = data['genre_opera'].map(lambda x: gergo2it[x] if x in gergo2it.keys() else x)
    
    print('step 1 done')
    
    # extract genre step 2
    nlp = spacy.load("it_core_news_sm")
    data['genre_vec_method_1'] = [np.mean(np.array([token.vector for token in nlp(loc)]), axis=0) 
                                  for loc in data.genre_opera]
    
    kmeans = KMeans(n_clusters=15, random_state=0, max_iter=50).fit(data['genre_vec_method_1'].tolist())
    data['predicted_genre_cluster_method_1'] = data['genre_vec_method_1'].apply(lambda x: kmeans.predict([x.tolist()])[0])
    
    # predict genre based on cluster
    cluster_genre = {}
    for i, cluster in enumerate(data.predicted_genre_cluster_method_1):
        if cluster in cluster_genre.keys():
            if data.genre_opera[i] != 'Not found':
                cluster_genre[cluster].append(data.genre_opera[i])
        else:
            cluster_genre[cluster] = [data.genre_opera[i]]

    for k in cluster_genre.keys():
        cluster_genre[k] = max(set(cluster_genre[k]), key=cluster_genre[k].count)
        
    data['inferred_genre'] = [cluster_genre[cluster] for cluster in data.predicted_genre_cluster_method_1]
    
    print('step 2 done')
    
    data = data.drop(columns=['genre_opera', 'genre_vec_method_1', 'predicted_genre_cluster_method_1', 'genre_mediawiki_pageid'])
    
    print(data.sample(5))
    print('Number of rows for which no genre was found:', data[data['inferred_genre'] == 'Not found'].shape, 
          ' over the total number of rows:', data.shape)
    
    data.to_csv(output_file, sep='\t')
    
    
if __name__ == "__main__":
    input_file = 'data/librettos_05.csv'
    output_file = 'data/librettos_06.csv'
    main(input_file, output_file)    





    