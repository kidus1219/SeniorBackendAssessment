import random
import pycountry
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from users.models import User, Country
from blogs.models import Blog
from analytics.models import BlogView

fake = Faker()


def random_past_date(days=5 * 365):
    offset = random.randint(0, days)
    return timezone.now() - timedelta(days=offset)


def random_between(start, end):
    total_seconds = int((end - start).total_seconds())
    offset = random.randint(0, total_seconds)
    return start + timedelta(seconds=offset)

def random_country():
    c = random.choice(list(pycountry.countries))
    return c.name, c.alpha_2


class Command(BaseCommand):
    help = "Seed dummy data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding dummy data...")

        # Countries
        countries = []
        for _ in range(20):
            name, code = random_country()
            country, _ = Country.objects.get_or_create(
                code=code,
                defaults={"name": name}
            )
            countries.append(country)

        # Users
        users = []
        for _ in range(50):
            user, _ = User.objects.get_or_create(
                username=fake.user_name() + str(random.randint(1, 9999)),
                defaults={
                    "first_name": fake.first_name(),
                    "email": fake.email(),
                    "country": random.choice(countries),
                },
            )
            users.append(user)

        # Blogs
        blogs = []
        for _ in range(200):
            created_at = random_past_date()
            blog = Blog.objects.create(
                title=fake.sentence(nb_words=6),
                author=random.choice(users),
                created_at=created_at
            )
            blogs.append(blog)

        # BlogViews - should never be older than the blog itself
        now = timezone.now()
        for _ in range(1000):
            blog = random.choice(blogs)
            BlogView.objects.create(
                blog=blog,
                ip_address=fake.ipv4(),
                created_at=random_between(blog.created_at, now)
            )

        # Special cases
        User.objects.get_or_create(
            username="user_no_blog",
            defaults={"first_name": "NoBlog", "country": random.choice(countries)}
        )

        Blog.objects.get_or_create(
            title="No views blog",
            defaults={"author": random.choice(users), "created_at": random_past_date()}
        )

        Country.objects.get_or_create(name="EmptyLand", code="EL")

        self.stdout.write(self.style.SUCCESS("Seeding complete"))
