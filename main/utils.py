import logging
import re
import requests
from urllib.parse import quote
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django_ratelimit.exceptions import Ratelimited
from django.middleware.csrf import get_token

logger = logging.getLogger("django")

class AddisLogFormatter(logging.Formatter):
    default_time_format = "%d/%b/%Y %H:%M:%S"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        if self.uses_server_time() and not hasattr(record, "server_time"):
            record.server_time = self.formatTime(record, self.datefmt)

        if hasattr(record, 'request') and hasattr(record.request, 'user'):
            user = record.request.user
            record.user = f"{user.first_name} - @{user.username} - #i{user.id}" if user.is_authenticated else 'Anonymous'
        else:
            record.user = 'N/A'

        return super().format(record)

    def uses_server_time(self):
        return self._fmt.find("{server_time}") >= 0


# TelegramNotificationLog uses AddisLogFormatter
class TelegramNotificationLog(logging.Handler):
    def __init__(self):
        super().__init__()
        self.BOT_TOKEN = "" # this is where i put the bot token to be used to send the logs to the common channel
        self.CHANNEL_ID = "" # the telegram channel id where the logs will be sent

    def emit(self, record):
        try:
            url_req = "https://api.telegram.org/bot" + self.BOT_TOKEN + "/sendMessage" + "?chat_id=" + str(self.CHANNEL_ID) + "&text=" + quote(self.format(record))
            requests.get(url_req, timeout=5)
        except Exception as e:
            logger.error("Error: TelegramNotificationLog => " + str(e)) # todo - will this create an infinite loop? check later, yeah maybe use another logger that only write to the debug file


class EnsureCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # For safe methods, trigger CSRF cookie generation
        if request.method in ("GET", "HEAD", "OPTIONS"):
            get_token(request)
        return self.get_response(request)


def ratelimit_handler(request, exception=None):
    if isinstance(exception, Ratelimited):
        return JsonResponse({'status': 0, 'message': 'Rate limit exceeded. You have sent too many requests in a short period of time.'}, status=429)
    return HttpResponseForbidden('Forbidden')


def dynamic_filter_parser(filter_str):
    filter_str = filter_str.strip()
    m = re.match(r'^(and|or|not)\((.*)\)$', filter_str)
    if m:
        op, inner = m.groups()
        conditions = split_conditions(inner)
        q_objects = [dynamic_filter_parser(c) for c in conditions]
        if op == "and":
            q = Q()
            for qo in q_objects:
                q &= qo
            return q
        elif op == "or":
            q = Q()
            for qo in q_objects:
                q |= qo
            return q
        elif op == "not":
            if len(q_objects) != 1:
                raise ValueError("not() accepts exactly one condition")
            return ~q_objects[0]
    else:
        # Base condition: field:op:value
        parts = filter_str.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid condition: {filter_str}")
        field, op, value = parts
        if op == "eq":
            return Q(**{field: value})
        elif op == "ne":
            return ~Q(**{field: value})
        elif op == "gt":
            return Q(**{f"{field}__gt": value})
        elif op == "gte":
            return Q(**{f"{field}__gte": value})
        elif op == "lt":
            return Q(**{f"{field}__lt": value})
        elif op == "lte":
            return Q(**{f"{field}__lte": value})
        elif op == "in":
            values = value.split("|")
            return Q(**{f"{field}__in": values})
        else:
            raise ValueError(f"Unsupported operator: {op}")


def split_conditions(inner):
    conditions = []
    depth = 0
    current = []
    for char in inner:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            conditions.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        conditions.append("".join(current).strip())
    return conditions
