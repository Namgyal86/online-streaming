from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise.dump import dump, load
import pandas as pd
from movies_and_user.models import Review, Movie
import os
from django.conf import settings

# Set the model path within the 'Recommendation' directory
MODEL_PATH = os.path.join(settings.BASE_DIR, 'movies_and_user', 'Recommendation', 'svd_model.pkl')


def train_collaborative_model():
    reviews = Review.objects.all().values('user_id', 'movie_id', 'rating')
    df = pd.DataFrame(list(reviews))

    if df.empty or not all(col in df.columns for col in ['user_id', 'movie_id', 'rating']):
        print("Not enough data to train the collaborative model.")
        return None  # Explicitly return None when data is insufficient

    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df[['user_id', 'movie_id', 'rating']], reader)
    trainset = data.build_full_trainset()

    algo = SVD(n_factors=50, n_epochs=30, lr_all=0.005, reg_all=0.1)

    try:
        algo.fit(trainset)
        dump(MODEL_PATH, algo=algo)
        print("Collaborative model trained and saved successfully.")
        return algo
    except Exception as e:
        print(f"Error training collaborative model: {e}")
        return None  # Return None if training fails

def collaborative_filtering_recommendations(user_id, top_n=10):
    try:
        algo, _ = load(MODEL_PATH)
        print("Model loaded successfully.")
    except FileNotFoundError:
        print("Model not found. Training a new one...")
        algo = train_collaborative_model()
    except Exception as e:
        print(f"Error loading the model: {e}")
        algo = None

    if algo is None:
        print("Collaborative filtering model not available. Skipping recommendations.")
        return []

    reviews = Review.objects.all().values('user_id', 'movie_id', 'rating')
    df = pd.DataFrame(list(reviews))

    rated_movie_ids = df[df['user_id'] == user_id]['movie_id'].tolist()
    all_movie_ids = set(Movie.objects.values_list('movie_id', flat=True))
    unrated_movie_ids = list(all_movie_ids - set(rated_movie_ids))

    if not unrated_movie_ids:
        print("No unrated movies found for the user.")
        return []

    predictions = []
    for movie_id in unrated_movie_ids:
        try:
            prediction = algo.predict(user_id, movie_id)
            predictions.append(prediction)
        except Exception as e:
            print(f"Error predicting for movie_id={movie_id}: {e}")

    if not predictions:
        print("No valid predictions could be made.")
        return []

    top_predictions = sorted(predictions, key=lambda x: x.est, reverse=True)
    recommended_movie_ids = [pred.iid for pred in top_predictions[:top_n]]

    print(f"Recommended movies for user {user_id}: {recommended_movie_ids}")
    return recommended_movie_ids



