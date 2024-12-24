from django.shortcuts import render,redirect
from movies_and_user.models import Movie,User,Review,Subscription,Package
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import ExtractWeek
from django.utils import timezone
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseRedirect,JsonResponse

from django.contrib import messages

logger = logging.getLogger(__name__)
def home(request):
    if request.user.is_authenticated:
        logout(request)
    current_week_number = now().isocalendar().week
    user= request.user
    movies = Movie.objects.all()
    trending_movies = Movie.objects.annotate(week=ExtractWeek('release_date')).filter(week=current_week_number).order_by('-total_views')[:5]
    popular_movies = Movie.objects.order_by('-total_views','-rating')[:5]
    recently_added_movies = Movie.objects.order_by('-release_date')[:5]
    recent_comments = Review.objects.select_related('movie', 'user').order_by('-review_id')[:4]
    categories = Movie.CATEGORY_CHOICES

    # Log details for debugging
    for movie in movies:
        logger.info(f"Movie Title: {movie.title}, Movie ID: {movie.movie_id}")


    

     # Get recommendations
    
    # 
     # Get the timeframe from query parameters
    timeframe = request.GET.get('timeframe', 'day')
    today = timezone.now()
    
    # Determine start date based on the selected timeframe
    if timeframe == 'day':
        start_date = today - timedelta(days=1)
    elif timeframe == 'week':
        start_date = today - timedelta(weeks=1)
    elif timeframe == 'month':
        start_date = today - timedelta(days=30)
    elif timeframe == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=1)  # Default to 'day' if invalid

    # Fetch top viewed movies based on the timeframe
    top_viewed_movies = Movie.objects.filter(release_date__gte=start_date).order_by('-total_views')[:5]

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render only the top-viewed movies section as HTML
        top_movies_html = render(request, 'partials/top_viewed_movies.html', {'top_viewed_movies': top_viewed_movies}).content.decode('utf-8')
        return JsonResponse({'top_movies_html': top_movies_html})


    context ={
        'user':user,
        'movies':movies,
        'trending_movies':trending_movies,
        'popular_movies':popular_movies,
        'recently_add_movies':recently_added_movies,
        'recent_comments':recent_comments,
        'top_viewed_movies': top_viewed_movies,
        'selected_timeframe': timeframe,
        'categories':categories}    
    
    return render(request, 'index.html',context)

def movies_detail_home(request,):
    movies = Movie.objects.all()
    return render(request, 'movies-details.html', {'movies':movies})

def movies_by_category_home(request, category_name):
    # Fetch movies based on the category name
    movies_in_category = Movie.objects.filter(category=category_name)
    
    context = {
        'category_name': category_name,
        'movies': movies_in_category,
    }
    
    return render(request, 'movies_by_category_home.html', context)



def blog_page(request):
    return render(request,'blog.html')



def view_all_trending_home(request):
    trending_movies = Movie.objects.order_by('-total_views')[:20]  # Example limit
    context = {
        'section_title': 'Trending Movies',
        'movies': trending_movies,
    }
    return render(request, 'view_all_home.html', context)

def view_all_popular_home(request):
    popular_movies = Movie.objects.order_by('-total_views','-rating')[:5]
    return render(request,'view_all_home.html',{'movies':popular_movies,'title':'Popular movies'})

def view_all_recently_add_home(request):
    recently_added_movies = Movie.objects.order_by('-release_date')[:5]
    return render(request,'view_all_home.html',{'movies':recently_added_movies,'title':'Recently add movies'})


def contact(request):
    return render(request,'contact.html')
