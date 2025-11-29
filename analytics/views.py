import re

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count, Q, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
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
