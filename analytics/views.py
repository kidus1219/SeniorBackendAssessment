from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Count, Q, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from blogs.models import Blog


class BlogViewsAnalytics(APIView):
    class InputSerializer(serializers.Serializer):
        object_type = serializers.ChoiceField(choices=["user", "country"], default="user")
        range = serializers.ChoiceField(choices=["week", "month", "year"], default="year")
        start_date = serializers.DateTimeField(required=False)
        end_date = serializers.DateTimeField(required=False)

        def validate(self, attrs):
            start = attrs.get("start_date")
            end = attrs.get("end_date")
            range_value = attrs.get("range")

            # both or none rule - only pass if both are provided or both are None
            if bool(start) != bool(end):
                raise serializers.ValidationError(
                    "Provide both start_date and end_date or none."
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

        if object_type == 'country':
            group_field = 'author__country__name'
        else:
            group_field = 'author__username'

        data = (
            Blog.objects
            .select_related('author', 'author__country')  # avoids extra queries per blog(N+1 problem)
            .values(x=F(group_field))
            .annotate(
                y=Count('id', distinct=True),
                z=Count('views', filter=Q(views__created_at__gte=start_date, views__created_at__lte=end_date))
            )
            .order_by('-z')
        )

        resp = {
            'object_type': object_type,
            'start_date': start_date,
            'end_date': end_date,
            'labels': "X = Object (User/Country), Y = Total Blogs, Z = Total Views",
            'data': data
        }

        return Response(resp)
