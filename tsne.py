import os
import sys
import gensim
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

skip = False
if len(sys.argv) > 1 and sys.argv[1] == 'skip':
    skip = True

MAXIMUM = int(os.environ['TSNE_MAXIMUM']) if 'TSNE_MAXIMUM' in os.environ else 10000
PLOT_MAXIMUM = int(os.environ['PLOT_MAXIMUM']) if 'PLOT_MAXIMUM' in os.environ else 100

imported = False
labels = []
xs = []
ys = []

if os.path.exists('./tsne.csv') and not skip:
    print("Loading saved data!")
    with open('./tsne.csv', 'r') as f:
        for line in f.readlines():
            components = line.split(',')
            labels.append(','.join(components[:-2]))
            xs.append(float(components[-2]))
            ys.append(float(components[-1]))
    imported = True
    print("Loaded saved data!")
else:
    # Load Google's pre-trained Word2Vec model.
    print("Loading model!")
    model = gensim.models.KeyedVectors.load_word2vec_format('./model/GoogleNews-vectors-negative300.bin.gz', binary=True)  
    print("Loaded model!")

    tokens = []

    i = 0
    for word in model.wv.vocab:
        tokens.append(model[word])
        labels.append(word)
        i += 1
        if i == MAXIMUM: break
    
    tsne_model = TSNE(perplexity=40, n_components=2, init='pca', n_iter=2500, random_state=23)
    new_values = tsne_model.fit_transform(tokens)

    for value in new_values:
        xs.append(value[0])
        ys.append(value[1])

if not imported:
    with open('./tsne.csv', 'w+') as f:
        for i in range(len(xs)):
            f.write('%s,%s,%s\n' % (labels[i], xs[i], ys[i]))

plt.figure(figsize=(16, 16)) 
for i in range(min(PLOT_MAXIMUM, len(xs))):
    plt.scatter(xs[i],ys[i])
    plt.annotate(labels[i],
                 xy=(xs[i], ys[i]),
                 xytext=(5, 2),
                 textcoords='offset points',
                 ha='right',
                 va='bottom')
plt.show()