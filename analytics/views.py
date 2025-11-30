import re
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count, Q, F, Func, DateTimeField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, TruncYear
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from analytics.models import BlogView
from blogs.models import Blog
from main.utils import dynamic_filter_parser


# API #1 - /analytics/blog-views/
class BlogViewsAnalytics(APIView):
    class InputSerializer(serializers.Serializer):
        object_type = serializers.ChoiceField(choices=["user", "country"], default="user")
        range = serializers.ChoiceField(choices=["week", "month", "year"], default="year")
        start_date = serializers.DateTimeField(required=False)
        end_date = serializers.DateTimeField(required=False)
        filter_blog_creation = serializers.BooleanField(required=False, default=False)
        filter = serializers.CharField(required=False)

        def validate_filter(self, value):
            # basic checks
            if not value.strip():
                raise serializers.ValidationError("Filter cannot be empty string")
            if re.search(r"[^a-zA-Z0-9_:(),|]", value):
                # allows letters, digits, colon, parentheses, comma, pipe
                raise serializers.ValidationError(
                    "Filter contains invalid characters"
                )
            # check parentheses balance
            if value.count("(") != value.count(")"):
                raise serializers.ValidationError("Unbalanced parentheses in filter")

            return value

        def validate(self, attrs):
            start = attrs.get("start_date")
            end = attrs.get("end_date")
            range_value = attrs.get("range")

            # both or none rule - only pass if both are provided or both are None
            if bool(start) != bool(end):
                raise serializers.ValidationError(
                    "Provide both start_date & end_date or omit both."
                )

            # if provided
            if start and end:
                if start > end:
                    raise serializers.ValidationError(
                        "start_date cannot be greater than end_date."
                    )
            else:
                # if not provided, calculate based on range - last week, last month or last year
                end = timezone.now()
                if range_value == "week":
                    start = end - relativedelta(weeks=1)
                elif range_value == "month":
                    start = end - relativedelta(months=1)
                else:
                    start = end - relativedelta(years=1)

                attrs["start_date"] = start
                attrs["end_date"] = end

            return attrs

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        object_type = params["object_type"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        filter_blog_creation = params["filter_blog_creation"]
        dynamic_filter_param = params.get("filter")

        qs = Blog.objects.select_related('author', 'author__country').all()

        # If filter_blog_creation is true, apply the date filter to Blog as well, not just for BlogViews
        if filter_blog_creation:
            qs = qs.filter(created_at__gte=start_date, created_at__lte=end_date)

        # Dynamic filtering based on additional user query params
        if dynamic_filter_param:
            try:
                parsed_filter = dynamic_filter_parser(dynamic_filter_param)
                qs = qs.filter(parsed_filter)
            except Exception as e:
                return Response({"detail": str(e)}, status=400)

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
    class InputSerializer(serializers.Serializer):
        top = serializers.ChoiceField(choices=["user", "country", "blog"], default="user")
        range = serializers.ChoiceField(choices=["week", "month", "year"], default="year")
        start_date = serializers.DateTimeField(required=False)
        end_date = serializers.DateTimeField(required=False)
        filter_blog_creation = serializers.BooleanField(required=False, default=False)
        filter = serializers.CharField(required=False)

        def validate_filter(self, value):
            # basic checks
            if not value.strip():
                raise serializers.ValidationError("Filter cannot be empty string")
            if re.search(r"[^a-zA-Z0-9_:(),|]", value):
                # allows letters, digits, colon, parentheses, comma, pipe
                raise serializers.ValidationError(
                    "Filter contains invalid characters"
                )
            # check parentheses balance
            if value.count("(") != value.count(")"):
                raise serializers.ValidationError("Unbalanced parentheses in filter")

            return value

        def validate(self, attrs):
            start = attrs.get("start_date")
            end = attrs.get("end_date")
            range_value = attrs.get("range")

            # both or none rule - only pass if both are provided or both are None
            if bool(start) != bool(end):
                raise serializers.ValidationError(
                    "Provide both start_date & end_date or omit both."
                )

            # if provided
            if start and end:
                if start > end:
                    raise serializers.ValidationError(
                        "start_date cannot be greater than end_date."
                    )
            else:
                # if not provided, calculate based on range - last week, last month or last year
                end = timezone.now()
                if range_value == "week":
                    start = end - relativedelta(weeks=1)
                elif range_value == "month":
                    start = end - relativedelta(months=1)
                else:
                    start = end - relativedelta(years=1)

                attrs["start_date"] = start
                attrs["end_date"] = end

            return attrs

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        top_type = params["top"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        filter_blog_creation = params["filter_blog_creation"]
        dynamic_filter_param = params.get("filter")

        # Initial QuerySet
        qs = Blog.objects.select_related('author', 'author__country').all()

        # If filter_blog_creation is true, apply the date filter to Blog as well, not just for BlogViews
        if filter_blog_creation:
            qs = qs.filter(created_at__gte=start_date, created_at__lte=end_date)

        if dynamic_filter_param:
            try:
                parsed_filter = dynamic_filter_parser(dynamic_filter_param)
                qs = qs.filter(parsed_filter)
            except Exception as e:
                return Response({"detail": str(e)}, status=400)

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


# API #3 - /analytics/performance/
class PerformanceAnalytics(APIView):
    class InputSerializer(serializers.Serializer):
        compare = serializers.ChoiceField(choices=["day", "week", "month", "year"], default="month")
        user = serializers.CharField(required=False)  # Optional field to filter results for a single user
        filter = serializers.CharField(required=False)

        def validate_filter(self, value):
            # basic checks
            if not value.strip():
                raise serializers.ValidationError("Filter cannot be empty string")
            if re.search(r"[^a-zA-Z0-9_:(),|]", value):
                # allows letters, digits, colon, parentheses, comma, pipe
                raise serializers.ValidationError(
                    "Filter contains invalid characters"
                )
            # check parentheses balance
            if value.count("(") != value.count(")"):
                raise serializers.ValidationError("Unbalanced parentheses in filter")

            return value

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

    # Helper function to map 'compare' to the correct Trunc function
    def get_trunc_function(self, compare_value):
        if compare_value == 'month':
            return TruncMonth
        elif compare_value == 'week':
            return TruncWeek
        elif compare_value == 'day':
            return TruncDay
        elif compare_value == 'year':
            return TruncYear
        raise ValueError("Invalid compare value.")

    def get(self, request):
        serializer = self.InputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        compare = params["compare"]
        start_date = params["start_date"]
        end_date = params["end_date"]
        user = params.get("user_id")
        dynamic_filter_param = params.get("filter")

        TruncFunc = self.get_trunc_function(compare)

        blogs_qs = Blog.objects.filter(created_at__gte=start_date)
        views_qs = BlogView.objects.filter(created_at__gte=start_date)

        # Apply user filter - using username
        if user:
            blogs_qs = blogs_qs.filter(author__username=user)
            views_qs = views_qs.filter(blog__author__username=user)

        # Apply dynamic filters
        if dynamic_filter_param:
            try:
                parsed_filter = dynamic_filter_parser(dynamic_filter_param)
                blogs_qs = blogs_qs.filter(parsed_filter)
            except Exception as e:
                return Response({"detail": str(e)}, status=400)

        # Query A: Group Blogs by Period
        blogs_data = (
            blogs_qs
            .annotate(period=TruncFunc('created_at'))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')
        )

        # Query B: Group Views by Period
        views_data = (
            views_qs
            .annotate(period=TruncFunc('created_at'))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')
        )

        # Merging Data - I used a defaultdict instead of a normal dictionary cause it's just easier for handling missing keys
        timeline = defaultdict(lambda: {'blogs': 0, 'views': 0})

        for item in blogs_data:
            timeline[item['period']]['blogs'] = item['count']

        for item in views_data:
            timeline[item['period']]['views'] = item['count']

        # Calculation Z
        final_final_data = []
        sorted_periods = sorted(timeline.keys())
        previous_views = 0
        date_format = {
            "day": "%b %d", "week": "Week %W", "month": "%b %Y", "year": "%Y"
        }.get(compare, "%Y")

        for period in sorted_periods:
            stats = timeline[period]
            current_views = stats['views']
            current_blogs = stats['blogs']

            if previous_views == 0:
                z_formatted = "N/A"
            else:
                growth = ((current_views - previous_views) / previous_views) * 100
                z_formatted = f"{growth:+.1f}%"

            final_final_data.append({
                'x': f"{period.strftime(date_format)} ({current_blogs} Blogs)",
                'y': current_views,
                'z': z_formatted
            })

            # here i gotta update previous for next iteration
            previous_views = current_views

        resp = {
            'compare': compare,
            'start_date': start_date,
            'end_date': end_date,
            'labels': "X = Period & Blogs Created, Y = Total Views, Z = Growth %",
            'data': final_final_data
        }
        return Response(resp)
