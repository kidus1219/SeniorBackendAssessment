from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from faker import Faker

from users.models import User, Country
from blogs.models import Blog
from analytics.models import BlogView

fake = Faker()

class Command(BaseCommand):
    help = "Seed dummy data for blogs, users, countries, and blog views"

    def handle(self, *args, **options):
        self.stdout.write("Seeding dummy data...")

        # --> Create countries
        countries = []
        for _ in range(10):
            name = fake.country()
            code = fake.country_code()
            country, _ = Country.objects.get_or_create(name=name, code=code)
            countries.append(country)

        # --> Create users
        users = []
        for _ in range(50):
            username = fake.user_name() + str(random.randint(1, 9999))
            country = random.choice(countries)
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": fake.first_name(),
                    "email": fake.email(),
                    "country": country,
                },
            )
            users.append(user)

        # --> Create blogs
        blogs = []
        for _ in range(200):
            author = random.choice(users)
            created_at = timezone.now() - timedelta(days=random.randint(0, 365))
            blog = Blog.objects.create(
                title=fake.sentence(nb_words=6),
                author=author,
                created_at=created_at
            )
            blogs.append(blog)

        # --> Create clustered blog views
        for _ in range(1000):
            blog = random.choice(blogs)
            days_since_creation = max((timezone.now() - blog.created_at).days, 1)
            # cluster more views in recent days
            view_day_offset = random.randint(0, days_since_creation)
            created_at = blog.created_at + timedelta(days=view_day_offset)
            BlogView.objects.create(
                blog=blog,
                ip_address=fake.ipv4(),
                created_at=created_at
            )

        # --> Zero-view entities
        # User with no blogs
        User.objects.get_or_create(username="user_no_blog", defaults={"first_name": "NoBlog", "country": random.choice(countries)})
        # Blog with no views
        Blog.objects.create(title="No views blog", author=random.choice(users), created_at=timezone.now() - timedelta(days=10))
        # Country with no users
        Country.objects.get_or_create(name="EmptyLand", code="EL")

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
