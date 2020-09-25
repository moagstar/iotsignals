from django.db.models import Func


class HoursInterval(Func):
    function = "make_interval"
    template = "%(function)s(hours:=%(expressions)s)"
