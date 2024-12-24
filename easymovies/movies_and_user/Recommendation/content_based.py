from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from nltk.stem import PorterStemmer
from movies_and_user.models import Movie, Review

def calculate_content_based_recommendations(user, top_n=10):
    # Fetch movies data
    movies = Movie.objects.all().values('movie_id', 'title', 'genre', 'director', 'actors', 'description', 'category')
    df = pd.DataFrame(list(movies))

    if df.empty:
        return []  # No data to recommend from

    # Preprocess using stemming
    stemmer = PorterStemmer()
    for col in ['genre', 'director', 'actors', 'description', 'category']:
        df[col] = df[col].fillna('').apply(lambda x: ' '.join(stemmer.stem(word) for word in x.split()))

    # Fetch user's preferences based on their reviews
    user_reviews = Review.objects.filter(user=user)
    preferred_genres = set()
    preferred_actors = set()

    for review in user_reviews:
        movie = review.movie
        preferred_genres.update(movie.genre.split(','))
        preferred_actors.update(movie.actors.split(','))

    # Add a preference score for genres and actors to enhance recommendations
    def preference_weight(row):
        score = 0
        if any(genre in row['genre'].split(',') for genre in preferred_genres):
            score += 3  # Higher weight for matching genres
        if any(actor in row['actors'].split(',') for actor in preferred_actors):
            score += 2  # Lower weight for matching actors
        return score

    df['preference_score'] = df.apply(preference_weight, axis=1)

    # Combine weighted features
    df['combined_features'] = (
        (df['genre'] + " ") * 4 +
        (df['actors'] + " ") * 3 +
        (df['director'] + " ") * 2 +
        (df['description'] + " ") * 1
    )

    # Vectorize the combined features
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_features'])

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Focus on movies reviewed by the user for similarity
    user_movie_indices = df[df['movie_id'].isin(user_reviews.values_list('movie_id', flat=True))].index

    # Aggregate similarity scores for all movies
    similarity_scores = {}
    for idx in user_movie_indices:
        for i, score in enumerate(cosine_sim[idx]):
            similarity_scores[i] = similarity_scores.get(i, 0) + score * (1 + df.loc[i, 'preference_score'])

    # Sort movies based on the aggregated similarity score
    sorted_movies = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
    recommended_movie_ids = [df.iloc[i[0]]['movie_id'] for i in sorted_movies[:top_n]]

    return recommended_movie_ids
