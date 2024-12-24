from django.contrib.auth import login, authenticate, get_user_model,logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import base64
import uuid
from django.urls import reverse
from django.http import HttpResponseRedirect,JsonResponse
import requests
import json
import random
from django.template.loader import render_to_string

from django.contrib import messages
from django.conf import settings
import logging
from django.db.models.functions import ExtractWeek
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta

from .forms import UserForm, MovieForm, ReviewForm, SubscriptionForm,PackageForm
from .models import Movie, Review, Payment, Subscription, Package, User
from .Recommendation.hybridalgorithm import hybrid_recommendations

logger = logging.getLogger(__name__)



# User Registration View
def register_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect('login_page')
        else:
            logger.error("Registration failed: %s", form.errors)
    else:
        form = UserForm()
    return render(request, 'signup.html', {'form': form})

# User Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            logger.info(f'User {username} logged in successfully.')
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid credentials")
            logger.warning(f'Invalid login attempt for user {username}')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login_page')

# User Dashboard
@login_required
def user_dashboard(request):
    current_week_number = now().isocalendar().week
    user= request.user
    movies = Movie.objects.all()
    trending_movies = Movie.objects.order_by('-total_views')[:5]
    popular_movies = Movie.objects.order_by('-total_views','-rating')[:5]
    recently_added_movies = Movie.objects.order_by('-release_date')[:5]
    recent_comments = Review.objects.select_related('movie', 'user').order_by('-review_id')[:4]
    active_subscription = Subscription.objects.filter(user=user,payment_status=True,start_date__lte=timezone.now(),end_date__gte=timezone.now()).exists()
    categories = Movie.CATEGORY_CHOICES

    # Log details for debugging
    for movie in movies:
        logger.info(f"Movie Title: {movie.title}, Movie ID: {movie.movie_id}")

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
    if user.is_authenticated:
        recommendations = hybrid_recommendations(user, top_n=5)
        if not recommendations:
            print("No recommendations available, selecting random movies.")
            recommendations = get_random_movies(recently_added_movies, top_viewed_movies, popular_movies, trending_movies, count=10)
        print(recommendations)

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
        'active_subscription':active_subscription,
        'recently_add_movies':recently_added_movies,
        'recent_comments':recent_comments,
        'top_viewed_movies': top_viewed_movies,
        'selected_timeframe': timeframe,
        'recommendations': recommendations,
        'categories':categories}    
    
    return render(request, 'user-dashboard.html',context)

def get_random_movies(recently_added, top_viewed, popular, trending, count=10):
    """Selects a random mix of movies from given movie lists."""
    
    all_movies = list(recently_added) + list(top_viewed) + list(popular) + list(trending)
    random.shuffle(all_movies)
    return all_movies[:count]


def view_all_recommendations(request):
    user = request.user
    recommendations =  hybrid_recommendations(user, top_n=5)   # All recommended movies
    context = {
        'user': user,
        'section_title': 'Recommended for You',
        'movies': recommendations,
    }
    return render(request, 'view_all.html', context)

def view_all_trending(request):
    trending_movies = Movie.objects.order_by('-total_views')[:20]  # Example limit
    context = {
        'section_title': 'Trending Movies',
        'movies': trending_movies,
    }
    return render(request, 'view_all.html', context)

def view_all_popular(request):
    popular_movies = Movie.objects.order_by('-total_views','-rating')[:5]
    return render(request,'view_all.html',{'movies':popular_movies,'title':'Popular movies'})

def view_all_recently_add(request):
    recently_added_movies = Movie.objects.order_by('-release_date')[:5]
    return render(request,'view_all.html',{'movies':recently_added_movies,'title':'Recently add movies'})

@login_required
def user_profile(request):
    user = request.user  # Get the currently logged-in user
    context = {
        'user': user,
    }
    return render(request, 'user-profile.html', context)


def movies_by_category(request, category_name):
    # Fetch movies based on the category name
    movies_in_category = Movie.objects.filter(category=category_name)
    
    context = {
        'category_name': category_name,
        'movies': movies_in_category,
    }
    
    return render(request, 'movies_by_category.html', context)



def movie_search(request):
    option = request.GET.get('option')
    textoption = request.GET.get('textoption')
    movies = Movie.objects.all()

    if option == 'name':
        movies = movies.filter(title__icontains=textoption)
    elif option == 'category':
        movies = movies.filter(category__iexact=textoption)
    elif option == 'year':
        movies = movies.filter(release_date__year=textoption)

    return render(request, 'search_results.html', {'movies': movies})

# Admin-only view restriction
def is_admin(user):
    return user.is_superuser

    
def admin_dashboard(request):
    total_users = User.objects.count()
    total_movies = Movie.objects.count()
    active_subscriptions = Subscription.objects.filter(status='active').count()
    successful_payments = Payment.objects.filter(status='success').count()

    # Get recent activities (e.g., 5 latest movies added)
    recent_activities = Movie.objects.all().order_by('-release_date')[:5]

    # Get upcoming tasks (e.g., expired subscriptions)
    upcoming_tasks = Subscription.objects.filter(end_date__lt=timezone.now(), status='active')
   
    context = {
        'total_users': total_users,
        'total_movies': total_movies,
        'active_subscriptions': active_subscriptions,
        'successful_payments': successful_payments,
        'recent_activities': recent_activities,
        'upcoming_tasks': upcoming_tasks
    }

    return render(request, 'admin-dashboard.html',context)

def is_ajax(request):
    """Utility function to check if the request is AJAX."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def handle_form_response(request, form, success_message, error_message, success_redirect, ajax_template):
    """Utility to handle form responses for both AJAX and standard requests."""
    if form.is_valid():
        instance = form.save()
        if is_ajax(request):
            return JsonResponse({'success': True, 'message': success_message})
        messages.success(request, success_message)
        return redirect(success_redirect)
    else:
        if is_ajax(request):
            rendered_form = render_to_string(ajax_template, {'form': form}, request)
            return JsonResponse({'success': False, 'form_html': rendered_form})
        messages.error(request, error_message)
        return None



@user_passes_test(is_admin)
def add_admin(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            admin = form.save(commit=False)
            admin.is_staff = True
            admin.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Admin added successfully!'})
            else:
                return redirect('admin_dashboard')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                rendered_form = render_to_string('partials/add-admin.html', {'form': form}, request)
                return JsonResponse({'success': False, 'form_html': rendered_form})
            else:
                return render(request, 'add-admin.html', {'form': form})
    else:
        form = UserForm()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'partials/add-admin.html', {'form': form})
        return render(request, 'add-admin.html', {'form': form})

@user_passes_test(is_admin)
def add_movies(request):
    """View to add a new movie."""
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        response = handle_form_response(
            request=request,
            form=form,
            success_message='Movie added successfully!',
            error_message='Error adding movie.',
            success_redirect='admin_dashboard',
            ajax_template='partials/add-movies.html',
        )
        if response:  # Handles form success or failure
            return response
    else:
        form = MovieForm()

    template = 'partials/add-movies.html' if is_ajax(request) else 'add-movies.html'
    return render(request, template, {'form': form})


@user_passes_test(is_admin)
def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    movie.delete()
    messages.success(request, 'Movie deleted successfully.')
    return redirect('movies-details')

def admin_search(request):
    search_type = request.GET.get('search_type')
    query = request.GET.get('query')
    movies, users = None, None

    if search_type == 'movie':
        movies = Movie.objects.filter(title__icontains=query)
    elif search_type == 'user':
        users = User.objects.filter(username__icontains=query)

    # Render a partial HTML if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin_search_results.html', {'movies': movies, 'users': users})
    else:
        # Full-page render if not AJAX
        return render(request, 'admin-dashboard.html', {'movies': movies, 'users': users})


# Movies Details View
def movies_detail(request,):
    movies = Movie.objects.all()
    return render(request, 'movies-details.html', {'movies':movies})

def about_movie(request, movie_id):
    # Get the movie based on the movie_id (or return a 404 error if not found)
    movie = get_object_or_404(Movie, movie_id=movie_id)
    # Pass the movie to the template
    return render(request, 'about_Movie.html', {'movie': movie})

# User Profile in Admin Dashboard

@user_passes_test(is_admin)
def admin_user_details(request):
    # Query all users except the admin user, prefetching subscription and payment details for efficiency
    user_details = User.objects.exclude(username="admin").prefetch_related(
        'subscription_set__package',  # To get the related package details of each subscription
        'payment_set'  # To get the user's payment history
    )

    # Add subscription and package details to each user
    for user in user_details:
        # Get the latest active subscription for the user
        user_subscription = user.subscription_set.filter(status='active').first()
        if user_subscription:
            # If the user has an active subscription, calculate remaining time
            user.remaining_days = (user_subscription.end_date - timezone.now()).days
            user.package_name = user_subscription.package.package_name
            user.package_price = user_subscription.package.package_price
            user.package_quality = user_subscription.package.streaming_quality
            user.package_devices = user_subscription.package.device_limit
            user.package_content = user_subscription.package.content_access_level
            user.package_parental_controls = 'Yes' if user_subscription.package.parental_controls else 'No'
        else:
            user.remaining_days = None  # No active subscription
            user.package_name = 'None'
            user.package_price = 0
            user.package_quality = 'N/A'
            user.package_devices = 0
            user.package_content = 'N/A'
            user.package_parental_controls = 'No'

        # Get the latest payment status
        user.latest_payment_status = user.payment_set.first().status if user.payment_set.exists() else 'No Payment'

    context = {'user_details': user_details}

    # AJAX request for user details page
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'user-details.html', context)

    # Main dashboard page with user details
    return render(request, 'admin-dashboard.html', context)


@user_passes_test(is_admin)
def add_package(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = PackageForm(request.POST)
        if form.is_valid():
            form.save()
            # Return a JSON response for AJAX
            return JsonResponse({'success': True, 'message': 'Package added successfully.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # Render the form normally if it's not an AJAX request
    form = PackageForm()
    packages = Package.objects.all()
    return render(request, 'partials/add_package.html', {'form': form, 'packages': packages})


@user_passes_test(is_admin)
def edit_package(request, package_id):
    package = get_object_or_404(Package, pk=package_id)
    if request.method == 'POST':
        form = PackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            return redirect('add-package')  # Redirect after editing
    else:
        form = PackageForm(instance=package)

    return render(request, 'edit_package.html', {'form': form, 'package': package})

@user_passes_test(is_admin)
def delete_package(request, package_id):
    package = get_object_or_404(Package, pk=package_id)
    package.delete()
    return redirect('add-package')  # Redirect back after deleting
# Admin Edit User
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    else:
        form = UserForm(instance=user)
    return render(request, 'editUser.html', {'form': form, 'user': user})

# Delete User (Admin Only)
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.username != 'admin':
        user.delete()
        messages.success(request, "User deleted successfully.")
    else:
        messages.error(request, "Cannot delete admin user.")
    return redirect('user_details')

# Add Review for Movie
@login_required
def add_review(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Save the review with the current logged-in user
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user  # Associate the review with the logged-in user
            review.save()
            return redirect('movie_stream', movie_id=movie.movie_id)  # Redirect to the movie stream page
    else:
        form = ReviewForm()

    return render(request, 'add_review.html', {'form': form, 'movie': movie})


# Movie Watch View with Subscription Check
@login_required(login_url='login_page')
def watch_movies(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    subscription = Subscription.objects.filter(user=request.user).last()

    if subscription and subscription.is_active():
        movie.increment_views()
        return redirect('movie_stream', movie_id=movie.movie_id)  # Redirect to streaming
    else:
        return redirect('subscription')


@login_required
def movie_stream(request,movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    
    # Pass the movie object to the template to access the video file
    context = {
        'movie': movie,
    }
    return render(request,'movie_stream.html',context)

# Recommendations
@login_required
def recommendation_view(request):
    user = request.user
    recommendations = hybrid_recommendations(user)
    trending_recommendations = recommendations.order_by('-total_views')[:5]  # Sample for trending
    popular_recommendations = recommendations.order_by('-rating')[:5]       # Sample for popular

    context = {
        'user': user,
        'recommendations': recommendations,
        'trending_recommendations': trending_recommendations,
        'popular_recommendations': popular_recommendations,
    }
    return render(request, 'recommendations.html', context)


# Add Subscription
@login_required
def subscription_page(request):
    user = request.user
    packages = Package.objects.all()

    # Check for active subscription
    active_subscription = Subscription.objects.filter(
        user=user,
        payment_status=True,
        end_date__gte=timezone.now()
    ).last()

    if active_subscription:
        if active_subscription.end_date >= timezone.now():
            messages.info(request, f"Your current subscription is active until {active_subscription.end_date}.")
            return render(request, 'subscription_page.html', {
                'active_subscription': active_subscription,
                'packages': packages,
            })

    if request.method == 'POST':
        package_id = request.POST.get('package_id')

        if not package_id:
            messages.error(request, "Package selection is required.")
            return redirect('subscription_page')

        try:
            package = Package.objects.get(package_id=package_id)
        except Package.DoesNotExist:
            messages.error(request, "Invalid package selected.")
            return redirect('subscription_page')

        subscription = Subscription.objects.create(
            user=user,
            package=package,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=package.duration_in_days),
            payment_status=False,  # Remains inactive until payment is confirmed
            order_id=f'ORDER-{user.pk}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        )

        return redirect('payment_page', subscription_id=subscription.subscription_id, package_id=package.package_id)

    context = {
        'packages': packages,
        'active_subscription': active_subscription,
        'now': timezone.now()
    }
    return render(request, 'subscription_page.html', context)

    
@login_required
def payment_page(request, subscription_id, package_id):
    # Fetch subscription and package
    subscription = get_object_or_404(Subscription, subscription_id=subscription_id, user=request.user)
    package = get_object_or_404(Package, package_id=package_id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method == 'esewa':
            return HttpResponseRedirect(reverse('esewa_payment', args=[subscription_id]))
        elif payment_method == 'khalti':
            return redirect('init_khalti_payment', subscription_id=subscription_id)

    context = {'subscription': subscription, 'package': package}
    return render(request, 'payment_page.html', context)

KHALTI_SECRET_KEY = "f4ad39d43a3c40949d94ec21e2a1cd24"
@csrf_exempt
def init_khalti_payment(request, subscription_id):
    """Initiate Khalti Payment"""
    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        return JsonResponse({'error': 'Subscription not found'}, status=404)

    url = "https://a.khalti.com/api/v2/epayment/initiate/"
    return_url = request.build_absolute_uri(reverse('verify_khalti',args=[subscription_id]))
    amount = float(subscription.package.package_price) * 100  # Amount in paisa

    payload = {
        "return_url": return_url,
        "website_url": request.build_absolute_uri(),
        "amount": amount,
        "purchase_order_id": str(uuid.uuid4()),
        "purchase_order_name": f"Subscription {subscription.package.package_name}",
        "customer_info": {
            "name": request.user.get_full_name(),
            "email": request.user.email,
            "phone": request.user.tel  # Assuming user profile has a phone field
        }
    }

    headers = {
        'Authorization': f'Key {KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        response_data = response.json()
        payment_url = response_data.get('payment_url')
        if payment_url:
            return redirect(payment_url)
    
    return render(request, 'payment_failed.html', {'error': 'Failed to initiate payment'})

def verify_khalti(request,subscription_id):
    """Verify Khalti Payment"""
    url = "https://a.khalti.com/api/v2/epayment/lookup/"
    pidx = request.GET.get('pidx')

    if pidx:
        headers = {
            'Authorization': f'Key {KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        data = json.dumps({'pidx': pidx})
        res = requests.post(url, headers=headers, data=data)

        if res.status_code == 200:
            new_res = res.json()
            if new_res.get('status') == 'Completed':
                subscription = get_object_or_404(Subscription, subscription_id=subscription_id)
                subscription.payment_status = True
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=subscription.package.duration_in_days)
                subscription.save()
                subscription.save()
                
                # Redirect to the subscription page or success page
                return redirect('subscription')

    return redirect('payment_failed')
    

def payment_failed(request, subscription_id):
    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        return render(request, 'payment_failed.html', {'error': 'Subscription not found.'})

    return render(request, 'payment_failed.html', {'subscription': subscription})

# Initiate eSewa Payment View
@login_required
def esewa_payment_page(request, subscription_id):
    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id, user=request.user)
    except Subscription.DoesNotExist:
        return render(request, 'payment_failed.html', {'error': 'Subscription not found.'})

    package = subscription.package
    amount = package.package_price
    esewa_merchant_id = settings.ESEWA_MERCHANT_ID

    # URL to handle return from eSewa
    success_url = request.build_absolute_uri(reverse('esewa_success', args=[subscription.subscription_id]))
    failure_url = request.build_absolute_uri(reverse('esewa_failure', args=[subscription.subscription_id]))

    # eSewa payment parameters
    esewa_payment_data = {
        'amt': amount,
        'pdc': 0,
        'psc': 0,
        'txAmt': 0,
        'tAmt': amount,
        'pid': f'SUB-{subscription.subscription_id}',
        'scd': esewa_merchant_id,
        'su': success_url,
        'fu': failure_url,
    }

    # Redirect to eSewa payment page with data
    esewa_payment_url = f"{settings.ESEWA_BASE_URL}?{'&'.join([f'{k}={v}' for k, v in esewa_payment_data.items()])}"
    return redirect(esewa_payment_url)

# Handle successful eSewa payment
@csrf_exempt
def esewa_success(request, subscription_id):
    refId = request.GET.get('refId')  # eSewa transaction reference ID

    subscription = Subscription.objects.get(subscription_id=subscription_id)
    package = subscription.package
    amount = package.package_price

    # Verify the transaction with eSewa
    verify_data = {
        'amt': amount,
        'scd': settings.ESEWA_MERCHANT_ID,
        'pid': f'SUB-{subscription.subscription_id}',
        'rid': refId,
    }

    response = requests.post(settings.ESEWA_VERIFY_URL, data=verify_data)
    if response.text.strip() == "Success":
        subscription.payment_status = True
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=package.duration_in_days)
        subscription.save()
        return redirect('subscription')  # Redirect to subscription page on success
    else:
        return redirect('esewa_failure', subscription_id=subscription_id)

# Handle failed eSewa payment
@csrf_exempt
def esewa_failure(request, subscription_id):
    return render(request, 'payment_failed.html', {'error': 'Payment failed. Please try again.'})


