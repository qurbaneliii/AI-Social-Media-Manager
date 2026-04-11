# FILE: apps/content-analysis/services/nlp_feature_extractor.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass
class NLPFeatures:
    tfidf_matrix: np.ndarray
    tfidf_terms: list[str]
    sentiment_scores: list[float]
    dominant_topics: list[str]
    embedding_vector: np.ndarray


class NLPFeatureExtractor:
    def __init__(self, nlp_model: object) -> None:
        self.nlp_model = nlp_model
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.topic_model = BERTopic(embedding_model=self.embedding_model, calculate_probabilities=False, verbose=False)
        self.vader = SentimentIntensityAnalyzer()

    async def process(self, texts: list[str]) -> NLPFeatures:
        """Extract TF-IDF terms, sentiment, topics, and a 768-dim embedding vector."""
        tfidf_sparse = self.vectorizer.fit_transform(texts)
        tfidf_matrix = tfidf_sparse.toarray()
        terms = self.vectorizer.get_feature_names_out().tolist()

        sentiments: list[float] = []
        for text in texts:
            score = 0.0
            doc = self.nlp_model(text)
            cats = getattr(doc, "cats", {})
            if cats:
                score = float(cats.get("positive", 0.0) - cats.get("negative", 0.0))
            else:
                score = float(self.vader.polarity_scores(text)["compound"])
            sentiments.append(score)

        topics, _ = self.topic_model.fit_transform(texts)
        dominant_topics = [f"topic_{int(topic)}" for topic in topics]

        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        centroid = embeddings.mean(axis=0).astype(np.float32)
        if centroid.shape[0] != 768:
            centroid = np.resize(centroid, 768).astype(np.float32)

        return NLPFeatures(
            tfidf_matrix=tfidf_matrix,
            tfidf_terms=terms,
            sentiment_scores=sentiments,
            dominant_topics=dominant_topics,
            embedding_vector=centroid,
        )
