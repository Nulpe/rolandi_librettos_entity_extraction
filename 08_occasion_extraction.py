import pandas as pd
import re
import numpy as np
import spacy
from sklearn.cluster import KMeans
from tqdm import tqdm

def main(input_file, output_file):
    
    # load input file
    data = pd.read_csv(input_file, delimiter='\t', index_col='file_name')
    
    # extract occasion step 1
    nlp = spacy.load("it_core_news_sm")

    data['occasion_method_1'] = [[ent.text
                                  for ent in nlp(title).ents
                                  if (ent.label_ == 'MISC' or ent.label_ == 'ORG')]
                                  for title in data.title 
                                  ]
    time = ('carnevale', 'carnovale', 'olimpiade', 'fiera')
    data['inferred_occasion'] = [[occasion for occasion in occasions if occasion.lower().startswith(time)] 
                                 for occasions in data.occasion_method_1]
    data['inferred_occasion'] = [occasion[0] if len(occasion) > 0 else 'Not found' 
                                 for occasion in data.inferred_occasion]
    data = data.drop(columns=['occasion_method_1'])
    
    print(data.sample(5))
    print('Number of rows for which no occasion was found:', data[data['inferred_occasion'] == 'Not found'].shape, 
          ' over the total number of rows:', data.shape)
    
    data.to_csv(output_file, sep='\t')
    
    
if __name__ == "__main__":
    input_file = 'data/librettos_06.csv'
    output_file = 'data/librettos_07.csv'
    main(input_file, output_file)    




 