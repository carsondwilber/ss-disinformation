import os
import sys
import gensim
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

MAXIMUM = int(os.environ['TSNE_MAXIMUM']) if 'TSNE_MAXIMUM' in os.environ else 10000  # noqa
PLOT_MAXIMUM = int(os.environ['PLOT_MAXIMUM']) if 'PLOT_MAXIMUM' in os.environ else 100  # noqa

model = gensim.models.KeyedVectors.load_word2vec_format('./model/GoogleNews-vectors-negative300.bin.gz', binary=True)  # noqa


def calculate_embeddings(phrase):
    if isinstance(phrase, str):
        phrase = phrase.split()
    elif not isinstance(phrase, list):
        raise Exception(
            "Must provide a string or list of strings to calculate an embedding.")

    embeddings = []

    for word in phrase[:min(len(phrase), MAXIMUM)]:
        if word in model.wv.vocab:
            embeddings.append(model[word])

    try:
        return calculate_average(embedding)
    except:
        raise Exception(
            "Failed to find enough valid tokens to parse as an embedding.")


def calculate_average(embeddings):
    if len(embeddings) < 2:
        raise Exception("Must provide at least two embeddings to average.")

    result = embeddings[0]
    for embedding in embeddings[1:min(len(embeddings), MAXIMUM)]:
        result = result + embedding

    return result / i


tsne_model = TSNE(perplexity=40, n_components=2,
                  init='pca', n_iter=2500, random_state=23)
new_values = tsne_model.fit_transform(tokens)

for value in new_values:
    xs.append(value[0])
    ys.append(value[1])

if not imported:
    with open('./tsne.csv', 'w+') as f:
        for i in range(len(xs)):
            f.write('%s,%s,%s\n' % (labels[i], xs[i], ys[i]))


def show_plot(xys):
    plt.figure(figsize=(16, 16))
    for i in range(min(PLOT_MAXIMUM, len(xs))):
        plt.scatter(xs[i], ys[i])
        plt.annotate(labels[i],
                     xy=(xs[i], ys[i]),
                     xytext=(5, 2),
                     textcoords='offset points',
                     ha='right',
                     va='bottom')
    plt.show()
