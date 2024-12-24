from movies_and_user.models import Movie
from .content_based import calculate_content_based_recommendations
from .collaborative import collaborative_filtering_recommendations

def hybrid_recommendations(user, top_n=10, content_weight=0.6, collab_weight=0.4):
    # Content-based recommendations
    content_recs = calculate_content_based_recommendations(user, top_n=top_n)

    # Collaborative recommendations
    collab_recs = collaborative_filtering_recommendations(user.id, top_n=top_n)

    # Combine recommendations with weighting
    rec_dict = {}
    for i, movie_id in enumerate(content_recs):
        rec_dict[movie_id] = rec_dict.get(movie_id, 0) + content_weight * (top_n - i)
    for i, movie_id in enumerate(collab_recs):
        rec_dict[movie_id] = rec_dict.get(movie_id, 0) + collab_weight * (top_n - i)

    # Sort by combined score and select top_n recommendations
    final_recs = sorted(rec_dict.items(), key=lambda x: x[1], reverse=True)
    final_recs = [movie_id for movie_id, score in final_recs[:top_n]]

    return Movie.objects.filter(movie_id__in=final_recs)
