from django.db import connection
import time

with connection.cursor() as cursor:
    while True:
        cursor.execute("""
            with size as (
                SELECT sum(pg_total_relation_size(psu.relid))::int                      AS total,
                       sum(pg_relation_size(psu.relid))::int                            AS internal,
                       sum(pg_table_size(psu.relid) - pg_relation_size(psu.relid))::int AS external, -- toast
                       sum(pg_indexes_size(psu.relid))::int                             AS indexes
                FROM pg_catalog.pg_statio_user_tables psu
                         JOIN pg_class pc ON psu.relname = pc.relname
                         JOIN pg_database pd ON pc.relowner = pd.datdba
                         JOIN pg_inherits pi ON pi.inhrelid = pc.oid
                WHERE pd.datname = 'iotsignals'
                  and pi.inhparent = 'passage_passage'::regclass
                GROUP BY pi.inhparent
                ORDER BY sum(pg_total_relation_size(psu.relid)) DESC
            )
            , count as (
                select count(passage_passage.*) as count
                from passage_passage
            )
            select size.*, count.*
            from size, count
        """)
        print(' '.join(map(str, cursor.fetchone())))
        time.sleep(10)
