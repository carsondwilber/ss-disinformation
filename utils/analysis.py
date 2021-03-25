import os
import sys
import gensim
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

model = gensim.models.KeyedVectors.load_word2vec_format(
    './model/GoogleNews-vectors-negative300.bin.gz', binary=True)


def mean_vector(words, max_words=100):
    valid_words = 0
    vector = None

    for word in words[:min(max_words, len(words))]:
        if word in model:
            valid_words += 1
            if valid_words == 1:
                vector = model[word]
            else:
                vector += model[word]

    if valid_words == 0:
        raise Exception("No valid words provided for mean vector.")

    return vector / valid_words


class Entity:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label


def generate_entities(vectors, labels):
    tsne_model = TSNE(perplexity=40, n_components=2,
                      init='pca', n_iter=2500, random_state=23)
    coordinates = tsne_model.fit_transform(vectors)

    entities = []
    for xy, l in zip(coordinates, labels):
        entities.append(Entity(xy[0], xy[1], label))

    return entities


def generate_plot(entities, max_plot=100):
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
