import os
import sys

import gensim
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from utils.configuration import Configurable
from utils.log import Logging

model = gensim.models.KeyedVectors.load_word2vec_format('./data/models/GoogleNews-vectors-negative300.bin.gz', binary=True)  # noqa


class PlotEntity:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label


class Analysis(Logging, Configurable):
    ''' TODO: add configurable defaults for plots and mean vector approach '''

    @classmethod
    def mean_vector(cls, words: list, max_words: int = 100):
        valid_words = 0
        vector = None

        for word in words[:min(max_words, len(words))]:
            if word in model:
                valid_words += 1
                if valid_words == 1:
                    vector = model[word]
                else:
                    vector = vector + model[word]

        if valid_words == 0:
            raise Exception("No valid words provided for mean vector.")

        return vector / valid_words

    @classmethod
    def generate_entities(cls, vectors: list, labels: list):
        if not len(vectors) == len(labels):
            raise Exception("Must provide same number of vectors and labels.")

        tsne_model = TSNE(perplexity=40, n_components=2,
                          init='pca', n_iter=2500, random_state=23)

        coordinates = tsne_model.fit_transform(vectors)

        entities = []
        for xy, label in zip(coordinates, labels):
            if not isinstance(xy[0], (int, float)):
                raise Exception("Coordinates must be numerical values.")
            if not isinstance(label, str):
                raise Exception("Labels must be string values.")
            entities.append(PlotEntity(xy[0], xy[1], label))

        return entities

    @classmethod
    def generate_plot(cls, entities, max_plot=100):
        plt.figure(figsize=(16, 16))

        for entity in entities[:min(max_plot, len(entities))]:
            plt.scatter(entity.x, entity.y)
            plt.annotate(entity.label,
                         xy=(entity.x, entity.y),
                         xytext=(5, 2),
                         textcoords='offset points',
                         ha='right',
                         va='bottom')

        return plt
