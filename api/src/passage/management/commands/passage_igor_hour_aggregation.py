import datetime
import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import connection

log = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) argument
        parser.add_argument(
            '--from-date',
            type=datetime.date.fromisoformat,
            help='Run the aggregations from this date',
        )

    def _get_delete_query(self, run_date):
        return f""" 
        DELETE FROM passage_heavytraffichouraggregation
        WHERE passage_at_year = {run_date.year}
        AND passage_at_month = {run_date.month}
        AND passage_at_day = {run_date.day}
        ;
        """

    def _get_aggregation_query(self, run_date):
        return f"""
            INSERT INTO passage_igorhouraggregation (
                passage_at_timestamp,
                passage_at_date,
                passage_at_year,
                passage_at_month,
                passage_at_day,
                passage_at_week,
                passage_at_day_of_week,
                passage_at_hour,
                order_kaart,
                order_naam,
                cordon,
                richting,
                location,
                geom,
                azimuth,
                kenteken_land,
                taxi_indicator,
                europese_voertuigcategorie,
                intensiteit
            )
            
            -- query voor IGOR en Druktebeeld
            SELECT
                date_trunc('hour', p.passage_at) AS timestamp,
                date(p.passage_at) AS date,
                extract(YEAR FROM p.passage_at)::int AS year,
                extract(MONTH FROM p.passage_at)::int AS month,
                extract(DAY FROM p.passage_at)::int AS day,
                extract(WEEK FROM p.passage_at)::int AS week,
                CASE
                    WHEN extract(DOW FROM p.passage_at)::int = 0 then '7 zondag'
                    WHEN extract(DOW FROM p.passage_at)::int = 1 then '1 maandag'
                    WHEN extract(DOW FROM p.passage_at)::int = 2 then '2 dinsdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 3 then '3 woendsag'
                    WHEN extract(DOW FROM p.passage_at)::int = 4 then '4 donderdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 5 then '5 vrijdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 6 then '6 zaterdag'
                ELSE 'onbekend ' END AS dow,
                extract(HOUR FROM p.passage_at)::int AS hour,
                --  blok camera informatie
                h.order_kaart,
                h.order_naam,
                h.cordon,
                h.richting,
                h.location,
                h.geom,
                h.azimuth,
                --  blok voertuig informatie
                p.kenteken_land,
                p.taxi_indicator,
                p.europese_voertuigcategorie,
                --  blok intensiteit informatie
                count(*) as intensiteit
        
                from passage_passage AS p
                left join	passage_camera AS h
                on			p.camera_naam = h.camera_naam AND
                            p.camera_kijkrichting = h.camera_kijkrichting AND
                            p.rijrichting = h.rijrichting
                WHERE passage_at >= '{run_date}'
                AND passage_at < '{run_date + timedelta(days=1)}'
                AND h.cordon  in ('S100','A10')
        
        
                group by
                
                date_trunc('hour', p.passage_at),
                date(p.passage_at),
                extract(YEAR FROM p.passage_at),
                extract(MONTH FROM p.passage_at),
                extract(DAY FROM p.passage_at),
                extract(WEEK FROM p.passage_at),
                CASE
                    WHEN extract(DOW FROM p.passage_at)::int = 0 then '7 zondag'
                    WHEN extract(DOW FROM p.passage_at)::int = 1 then '1 maandag'
                    WHEN extract(DOW FROM p.passage_at)::int = 2 then '2 dinsdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 3 then '3 woendsag'
                    WHEN extract(DOW FROM p.passage_at)::int = 4 then '4 donderdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 5 then '5 vrijdag'
                    WHEN extract(DOW FROM p.passage_at)::int = 6 then '6 zaterdag'
                ELSE 'onbekend ' END,
                extract(HOUR FROM p.passage_at),
                --  blok camera informatie
                h.order_kaart,
                h.order_naam,
                h.cordon,
                h.richting,
                h.geom,
                h.location,
                h.azimuth,
                p.kenteken_land,
                p.taxi_indicator,
                p.europese_voertuigcategorie;
        """

    def _run_query_from_date(self, run_date):
        log.info(f"Delete previously made aggregations for date {run_date}")
        delete_query = self._get_delete_query(run_date)
        log.info(f"Run the following query: {delete_query}")
        with connection.cursor() as cursor:
            cursor.execute(delete_query)
            log.info(f"Deleted {cursor.rowcount} records")

        log.info(f"Run aggregation for date {run_date}")
        aggregation_query = self._get_aggregation_query(run_date)
        log.info(f"Run the following query: {aggregation_query}")
        with connection.cursor() as cursor:
            cursor.execute(aggregation_query)
            log.info(f"Inserted {cursor.rowcount} records")

    def handle(self, *args, **options):
        if options['from_date']:
            run_date = options['from_date']
            while run_date < date.today():
                self._run_query_from_date(run_date)
                run_date = run_date + timedelta(days=1)

        else:
            run_date = date.today() - timedelta(days=1)
            self._run_query_from_date(run_date)
