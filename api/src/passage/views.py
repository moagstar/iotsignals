# std
from datetime import timedelta
# 3rd party
from contrib.rest_framework.authentication import SimpleTokenAuthentication
from django.db.models import DateTimeField, ExpressionWrapper, F, Sum
from django.utils import timezone
from django_filters.filterset import filterset_factory
from passage.case_converters import to_snakecase
from passage.expressions import HoursInterval
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
# iotsignals
from writers import CSVExport
from . import models, serializers


class PassageViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):

    serializer_class = serializers.PassageDetailSerializer
    serializer_detail_class = serializers.PassageDetailSerializer

    # override create to convert request.data from camelcase to snakecase.
    def create(self, request, *args, **kwargs):
        tmp = {to_snakecase(k): v for k, v in request.data.items()}
        request.data.clear()
        request.data.update(tmp)
        return super().create(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='export-taxi')
    def export_taxi(self, request, *args, **kwargs):
        # 1. Get the iterator of the QuerySet
        qs = (
            models.PassageHourAggregation.objects.annotate(datum=F('date'))
            .values('datum')
            .annotate(aantal_taxi_passages=Sum('count'))
            .filter(taxi_indicator=True)
        )

        # 2. Create the instance of our CSVExport class
        csv_export = CSVExport()

        # 3. Export (download) the file
        #  return csv_export.export(
        #  "export",
        #  iterator,
        #  lambda x: [x['datum'], x['aantal_taxi_passages']],
        #  header=['datum', 'aantal_taxi_passages'],
        #  )

        return csv_export.export("export", qs.iterator(), streaming=True)

    @action(
        methods=['get'],
        detail=False,
        url_path='export',
        authentication_classes=[SimpleTokenAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def export(self, request, *args, **kwargs):
        # 1. Get the iterator of the QuerySet
        previous_week = timezone.now() - timedelta(days=timezone.now().weekday(), weeks=1)
        year = previous_week.year
        week = previous_week.isocalendar()[1]

        Filter = filterset_factory(
            models.PassageHourAggregation, fields=['year', 'week']
        )
        qs = Filter(request.GET).qs

        # If no date has been given, we return the data of last week
        # Since the last week of the year can contain days of both years
        # we will search in both years.
        if not request.GET.get('year') and not request.GET.get('week'):
            monday = previous_week
            sunday = monday + timedelta(days=6)
            qs = qs.filter(date__gte=monday, date__lte=sunday)

        qs = (
            qs.annotate(
                bucket=ExpressionWrapper(
                    F("date") + HoursInterval(F("hour")), output_field=DateTimeField()
                ),
            )
            .values("camera_id", "camera_naam", "bucket")
            .annotate(sum=Sum("count"))
            .order_by("bucket")
        )

        # 2. Create the instance of our CSVExport class
        csv_export = CSVExport()

        # 3. Export (download) the file
        return csv_export.export("export", qs.iterator(), streaming=True)
