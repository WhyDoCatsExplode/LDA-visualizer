"""Export a fitted Python LDA for the LDA topic modelling toolkit.

Use the function for your library, then open the page, click "Import model"
and pick the JSON. Pass `texts` (the original documents) to enable the
per-word document view, or select the .txt files together with the JSON.

    export_sklearn(lda, vectorizer, X, names, texts)
    export_gensim(lda, corpus, names, texts)
"""
import json

import numpy as np


def _sig(rows):
    # 6 significant digits keeps tiny probabilities (rounding to 6 decimals would zero them).
    return [[float(f"{v:.6g}") for v in row] for row in rows]


def _write(path, source, terms, phi, names, theta, tokens, texts):
    out = {
        "format": "lda-toolkit", "version": 1, "source": source,
        "terms": [str(t) for t in terms],
        "phi": _sig(phi),                # K × V: p(w | z), β in the article
        "docs": [str(n) for n in names],
        "theta": _sig(theta),            # D × K: topic mixtures (θ)
        "tokens": [int(t) for t in tokens],
    }
    if texts is not None:
        out["texts"] = [str(t) for t in texts]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)


def export_sklearn(lda, vectorizer, X, names, texts=None, path="lda_model.json"):
    """lda: fitted LatentDirichletAllocation; X: the document-term matrix it was fit on."""
    # components_ are unnormalised pseudo-counts; each row becomes p(word | topic).
    phi = lda.components_ / lda.components_.sum(axis=1, keepdims=True)
    theta = lda.transform(X)
    tokens = np.asarray(X.sum(axis=1)).ravel()
    _write(path, "Python · scikit-learn", vectorizer.get_feature_names_out(), phi, names, theta, tokens, texts)


def export_gensim(lda, corpus, names, texts=None, path="lda_model.json"):
    """lda: fitted gensim LdaModel; corpus: the bag-of-words list it was trained on."""
    phi = lda.get_topics()               # rows already sum to 1
    terms = [lda.id2word[i] for i in range(lda.num_terms)]
    # get_document_topics drops tiny topics even at minimum_probability=0, so fill a dense row.
    theta = []
    for bow in corpus:
        row = [0.0] * lda.num_topics
        for k, p in lda.get_document_topics(bow, minimum_probability=0.0):
            row[k] = float(p)
        theta.append(row)
    tokens = [sum(c for _, c in bow) for bow in corpus]
    _write(path, "Python · gensim", terms, phi, names, theta, tokens, texts)
