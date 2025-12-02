from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import serializers

class BaseAnalyticsInputSerializer(serializers.Serializer):
    #Base serializer for analytics endpoints that share common date range logic.

    range = serializers.ChoiceField(choices=["week", "month", "year"], default="year")
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    filter_blog_creation = serializers.BooleanField(required=False, default=False)

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
