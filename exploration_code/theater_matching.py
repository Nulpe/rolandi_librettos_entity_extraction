import spacy
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from tqdm import tqdm

tqdm.pandas()

nlp = spacy.load("it_core_news_sm")

from nltk.cluster import KMeansClusterer
import nltk

locations = pd.read_csv('data/librettos_1.csv')
locations = locations.fillna('NaN')
locations['location_vec'] = [np.mean(np.array([token.vector for token in nlp(loc)]), axis=0) for loc in locations.location]

print('Processed the set')

NUM_CLUSTERS = 150

# kclusterer = KMeansClusterer(NUM_CLUSTERS, distance=nltk.cluster.util.cosine_distance, repeats=100, avoid_empty_clusters=True)
# assigned_clusters = kclusterer.cluster(locations['location_vec'], assign_clusters=True)
# locations['predicted_cluster'] = kclusterer.cluster(locations['location_vec'], assign_clusters = True)
kmeans = KMeans(n_clusters=150, random_state=0, max_iter=500, verbose=10000).fit(locations['location_vec'].tolist())
# print(kmeans)

locations['predicted_cluster'] = locations['location_vec'].progress_apply(
	lambda x: kmeans.predict([x.tolist()])[0])




locations.to_csv('data/librettos_2.csv')
