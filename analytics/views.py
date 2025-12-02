import re
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count, Q, F, Sum, Case, IntegerField, When, Window, ExpressionWrapper, FloatField, Value, Subquery, OuterRef
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, TruncYear, Lag, Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django_filters import rest_framework as filters

from analytics.models import BlogView
from analytics.serializers import BaseAnalyticsInputSerializer
from blogs.models import Blog


# API #1 - /analytics/blog-views/
class BlogViewsAnalytics(APIView):
    class InputSerializer(BaseAnalyticsInputSerializer):
        object_type = serializers.ChoiceField(choices=["user", "country"], default="user")

    class InputFilterSet(filters.FilterSet):
        title = filters.CharFilter(lookup_expr="icontains")
        author = filters.CharFilter(field_name="author__name", lookup_expr="icontains")
        country = filters.CharFilter(field_name="author__country__name", lookup_expr="icontains")

        class Meta:
            model = Blog
            fields = ["title", "author", "country"]

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        object_type = params["object_type"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        filter_blog_creation = params["filter_blog_creation"]

        qs = Blog.objects.select_related('author', 'author__country').all()

        # If filter_blog_creation is true, apply the date filter to Blog as well, not just for BlogViews
        if filter_blog_creation:
            qs = qs.filter(created_at__gte=start_date, created_at__lte=end_date)

        # Dynamic filtering based on additional user query params
        filterset = self.InputFilterSet(request.query_params, queryset=qs)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)
        qs = filterset.qs

        if object_type == 'country':
            group_field = 'author__country__name'
        else:
            group_field = 'author__username'

        data = (
            qs
            .values(x=F(group_field))
            .annotate(
                y=Count('id', distinct=True),
                z=Count('views', filter=Q(views__created_at__gte=start_date, views__created_at__lte=end_date))
            )
            .order_by('-z')
        )

        resp = {
            'endpoint': '/analytics/blog-views/',
            'object_type': object_type,
            'start_date': start_date,
            'end_date': end_date,
            'labels': "X = Object (User/Country), Y = Total Blogs, Z = Total Views",
            'data': data
        }

        return Response(resp)


# API #2 - /analytics/top/
class TopListAnalytics(APIView):
    class InputSerializer(BaseAnalyticsInputSerializer):
        top = serializers.ChoiceField(choices=["user", "country", "blog"], default="user")

    class InputFilterSet(filters.FilterSet):
        title = filters.CharFilter(lookup_expr="icontains")
        author = filters.CharFilter(field_name="author__name", lookup_expr="icontains")
        country = filters.CharFilter(field_name="author__country__name", lookup_expr="icontains")

        class Meta:
            model = Blog
            fields = ["title", "author", "country"]

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        top_type = params["top"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        filter_blog_creation = params["filter_blog_creation"]

        # Initial QuerySet
        qs = Blog.objects.select_related('author', 'author__country').all()

        # If filter_blog_creation is true, apply the date filter to Blog as well, not just for BlogViews
        if filter_blog_creation:
            qs = qs.filter(created_at__gte=start_date, created_at__lte=end_date)

        filterset = self.InputFilterSet(request.query_params, queryset=qs)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)
        qs = filterset.qs

        # We define the x, y, and z based on the 'top' type
        if top_type == 'user':
            group_field = 'author__username'
            x_label = 'Username'
            y_label = 'Blogs Created'
        elif top_type == 'country':
            group_field = 'author__country__name'
            x_label = 'Country Name'
            y_label = 'Blogs in Country'
        else:  # top_type == 'blog'
            group_field = 'id'
            x_label = 'Blog ID'
            y_label = 'Blog Title'

        data = (
            qs
            .values(x=F(group_field))  # Group by the selected field (User, Country, or Title)
            .annotate(
                y=Count('id', distinct=True) if top_type != 'blog' else F('title'),
                z=Count('views', filter=Q(views__created_at__gte=start_date, views__created_at__lte=end_date))
            )
            .order_by('-z')
            [:10]  # Slice the QuerySet to return only the Top 10
        )

        resp = {
            'endpoint': '/analytics/top/',
            'top_type': top_type,
            'start_date': start_date,
            'end_date': end_date,
            'labels': f"X = {x_label}, Y = {y_label}, Z = Total Views",
            'data': data
        }

        return Response(resp)


class PerformanceAnalytics(APIView):
    class InputSerializer(serializers.Serializer):
        compare = serializers.ChoiceField(choices=["day", "week", "month", "year"], default="month")
        user = serializers.CharField(required=False)  # Optional field to filter results for a single user

        def validate(self, attrs):
            now = timezone.now()
            compare_value = attrs['compare']

            # Determine the reporting duration
            if compare_value == 'year':
                # Report on the last 5 years
                attrs['start_date'] = now - relativedelta(years=5)
            elif compare_value == 'month':
                # Report on the last 12 months
                attrs['start_date'] = now - relativedelta(months=12)
            elif compare_value == 'week':
                # Report on the last 52 weeks
                attrs['start_date'] = now - relativedelta(weeks=52)
            elif compare_value == 'day':
                # Report on the last 30 days
                attrs['start_date'] = now - relativedelta(days=30)

            attrs['end_date'] = now
            return attrs

    class InputFilterSet(filters.FilterSet):
        title = filters.CharFilter(field_name="blog__title", lookup_expr="icontains")
        author = filters.CharFilter(field_name="blog__author__name", lookup_expr="icontains")
        country = filters.CharFilter(field_name="blog__author__country__name", lookup_expr="icontains")

        class Meta:
            model = BlogView
            fields = ["title", "author", "country"]

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        compare = params["compare"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        user = params.get("user")

        TruncFunc = {'month': TruncMonth, 'week': TruncWeek, 'day': TruncDay, 'year': TruncYear}.get(compare, TruncMonth)

        qs = BlogView.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        if user:
            qs = qs.filter(blog__author__username=user)

        # Apply dynamic filters
        filterset = self.InputFilterSet(request.query_params, queryset=qs)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)
        qs = filterset.qs

        # Aggregate per period
        period_qs = (
            qs.annotate(period=TruncFunc('created_at'))
            .values('period')
            .annotate(
                views_count=Count('id'),
                blogs_count=Count('blog', distinct=True)
            )
            .order_by('period')
        )

        period_data = list(period_qs)
        date_format = {"day": "%b %d", "week": "Week %W", "month": "%b %Y", "year": "%Y"}.get(compare, "%Y")

        final_data = []
        previous_views = None
        for item in period_data:
            current_views = item['views_count']
            if previous_views in (None, 0):
                growth_display = "N/A"
            else:
                growth_value = ((current_views - previous_views) / previous_views) * 100
                growth_display = f"{growth_value:+.1f}%"

            final_data.append({
                'x': f"{item['period'].strftime(date_format)} ({item['blogs_count']} Blogs)",
                'y': current_views,
                'z': growth_display
            })
            previous_views = current_views

        resp = {
            'compare': compare,
            'start_date': start_date,
            'end_date': end_date,
            'labels': "X = Period & Blogs Created, Y = Total Views, Z = Growth %",
            'data': final_data
        }
        return Response(resp)
