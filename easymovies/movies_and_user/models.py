from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import Q,F
from django.utils import timezone

class User(AbstractUser):
    address = models.CharField(max_length=255)
    tel = models.BigIntegerField(null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Add related_name here to avoid conflict
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Add related_name here to avoid conflict
        blank=True,
    )
    REQUIRED_FIELDS = ['email', 'address']

class Movie(models.Model):
    CATEGORY_CHOICES = [
        ('action', 'Action'),
        ('drama', 'Drama'),
        ('comedy', 'Comedy'),
        ('thriller', 'Thriller'),
        ('horror', 'Horror'),
        ('sci-fi', 'Sci-Fi'),
        ('romance', 'Romance'),
        ('documentary', 'Documentary'),
        ('animation', 'Animation'),
        ('fantasy', 'Fantasy'),
        # Add more categories as needed
    ]
    movie_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, unique=True)
    release_date = models.DateField()
    total_views = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, help_text=_("Select the category of the movie"))
    director = models.CharField(max_length=100)
    actors = models.TextField(help_text=_("List of actors separated by commas"))
    description = models.TextField(help_text=('Description about movies'),default="No description available")
    genre = models.CharField(max_length=100, help_text=_("Genres separated by commas (e.g., Action, Sci-Fi)"))
    video_file = models.FileField(upload_to='movies/', help_text=_("Upload the movie file in a supported format"))
    thumbnail = models.ImageField(upload_to='thumbnails/', help_text=_("Upload a thumbnail image for the movie"))
    cover_image = models.ImageField(upload_to='cover_images/', help_text=_("Optional cover image for the movie"), blank=True, null=True)

    def __str__(self):
        return self.title
    
    def increment_views(self):
        """Increment the view count for this movie."""
        self.total_views = F('total_views') + 1
        self.save(update_fields=['total_views'])
        self.refresh_from_db()

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        help_text=_("Rate between 1 and 5"))
    commentary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Review {self.review_id} for {self.movie.title}"
    

class Package(models.Model):
    package_id = models.AutoField(primary_key=True)
    package_name = models.CharField(max_length=100)
    package_price = models.DecimalField(max_digits=10, decimal_places=2)
    streaming_quality = models.CharField(
        max_length=50,
        choices=[
            ('SD', 'Standard Definition'),
            ('HD', 'High Definition'),
            ('UHD', 'Ultra High Definition/4K')
        ],
        default='SD'
    )
    device_limit = models.PositiveIntegerField(
        help_text="Maximum number of devices that can be used simultaneously",
        default=1
    )
    content_access_level = models.CharField(
        max_length=50,
        choices=[
            ('limited', 'Limited Content'),
            ('standard', 'Standard Content'),
            ('full', 'Full Content Library')
        ],
        default='standard'
    )
    is_trial = models.BooleanField(default=False, help_text="Indicates if the package is a trial")
    duration_in_days = models.PositiveIntegerField(
        default=30,
        help_text="Duration of the subscription in days"
    )
    parental_controls = models.BooleanField(default=False, help_text="Includes parental control features")

    def __str__(self):
        return self.package_name

    def get_features(self):
        """Return a string representation of the package features."""
        return (
            f"Quality: {self.streaming_quality}, "
            f"Devices: {self.device_limit}, "
            f"Content: {self.content_access_level}, "
            f"Parental Controls: {'Yes' if self.parental_controls else 'No'}, "
            f"Trial: {'Yes' if self.is_trial else 'No'}"
        )    
    


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    subscription_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    payment_status = models.BooleanField(default=False)
    order_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(end_date__gte=F('start_date')), name='end_date_gte_start_date'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.package.package_name}' if self.package else 'No Package'

    def is_active(self):
        """Check if the subscription is currently active."""
        return self.payment_status and self.start_date <= timezone.now() <= self.end_date



class Payment(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    payment_id = models.CharField(max_length=255, unique=True)
    amount = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)  # Success or Failure
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.payment_id} - {self.user.username}'

