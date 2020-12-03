import pandas as pd
import re
import numpy as np
import spacy
from sklearn.cluster import KMeans
from tqdm import tqdm
import requests

def main(input_file, output_file):
    
    # load input file
    data = pd.read_csv(input_file, delimiter='\t', index_col='file_name')
    
    # title extraction step 1
    genre = r'''(?i)modi sacri |(?i)rappresentato con |(?i)dramma|(?i)drama|(?i)melodramma|(?i)melodrama|(?i)melo-dramma|(?i)oratorio|(?i)favola pastorale|(?i)fauola musicale|(?i)burletta in musica|(?i)componimento sagro|(?i)azione musicale|(?i)componimento sacro|(?i)per musica|(?i)opera|(?i)tragedia|(?i)spettacolo fantastico|(?i)scena in versi|(?i)fauola tragicomica|(?i)fauola pastorale|(?i)diuertimento comico|(?i)azione romantica|(?i)farsa|(?i)commeddia|(?i)commedia|(?i)operetta|(?i)festa|(?i)cantata|(?i)intermezzo in musica|(?i)intermezzi|(?i)favola in prosa|(?i)componimento sagro|(?i)componimento|(?i)azione sacra|(?i)actio sacra|(?i)fiaba|(?i)libretto fantastico|(?i)libretto|(?i)fauola|(?i)favola'''
    
    data['title_opera_method_1'] = [re.split(genre,s)[0].strip().strip(',').strip('.')
                                     if len(re.split(genre,s)) > 0 else 'Not found'
                                     for s in data.title]
    print('step 1 done')
    
    # title extraction step 2
    nlp = spacy.load("it_core_news_sm")
    
    data['title_opera_method_1'] = ['Not found' if loc == '' else loc for loc in data.title_opera_method_1]
    data['title_vec_method_1'] = [np.mean(np.array([token.vector for token in nlp(loc)]), axis=0) 
                                  for loc in data.title_opera_method_1]
    
    kmeans = KMeans(n_clusters=830, random_state=0, max_iter=50).fit(data['title_vec_method_1'].tolist())
    data['predicted_title_cluster_method_1'] = data['title_vec_method_1'].apply(lambda x: kmeans.predict([x.tolist()])[0])
    
    # infer title based on cluster
    cluster_title = {}
    for i, cluster in enumerate(data.predicted_title_cluster_method_1):
        if cluster in cluster_title.keys():
            if data.title_opera_method_1[i] != 'Not found':
                cluster_title[cluster].append(data.title_opera_method_1[i])
        else:
                cluster_title[cluster] = [data.title_opera_method_1[i]]
    
    for k in cluster_title.keys():
        cluster_title[k] = max(set(cluster_title[k]), key=cluster_title[k].count)
    
    data['inferred_title'] = [cluster_title[cluster] for cluster in data.predicted_title_cluster_method_1]
    
    data = data.drop(columns=['title_opera_method_1', 'title_vec_method_1',
                              'predicted_title_cluster_method_1', 'Unnamed: 0', 'Unnamed: 0.1', 'Unnamed: 0.1.1'])
    print('step 2 done')

    # title linking step 1
    ses = requests.Session()
    url = "https://it.wikipedia.org/w/api.php"

    data['title_mediawiki_pageid'] = [ses.get(url=url, params={"action": "query",
                                                               "format": "json",
                                                               "list": "search",
                                                               "srsearch": title}).json()
                                            ['query']['search'][0]['pageid'] 
                                       if ('query' in ses.get(url=url, params={"action": "query","format": "json",
                                                                             "list": "search","srsearch": title})
                                      .json().keys()) and (len(ses.get(url=url, params={"action": "query",
                                                                       "format": "json",
                                                                       "list": "search",
                                                                       "srsearch": title}).json()
                                              ['query']['search']) > 0)
                                       else
                                           'Not found'
                                       for title in data.inferred_title
                                       ]

    # extract information composer
    data['composer_mediawiki_pageid'] = [ses.get(url=url, params={"action": "query",
                                                               "format": "json",
                                                               "list": "search",
                                                               "srsearch": title}).json()
                                            ['query']['search'][0]['pageid'] 
                                       if ('query' in ses.get(url=url, params={"action": "query","format": "json",
                                                                             "list": "search","srsearch": title})
                                      .json().keys()) and (len(ses.get(url=url, params={"action": "query",
                                                                       "format": "json",
                                                                       "list": "search",
                                                                       "srsearch": title}).json()
                                              ['query']['search']) > 0)
                                       else
                                           'Not found'
                                       for title in data.inferred_composer
                                       ]
    
    print('step 3 done')
    
    print(data.sample(5))
    print('Number of rows for which no title was found:', data[data['inferred_title'] == 'Not found'].shape, 
          '\nnumber of rows for which no match to the title was found:', data[data['title_mediawiki_pageid'] == 'Not found'].shape,
          ' over the total number of rows:', data.shape)
    
    data.to_csv(output_file, sep='\t')
    
    
if __name__ == "__main__":
    input_file = 'data/librettos_04.csv'
    output_file = 'data/librettos_05.csv'
    main(input_file, output_file)    


