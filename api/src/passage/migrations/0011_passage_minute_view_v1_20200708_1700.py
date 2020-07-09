from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('passage', '0010_auto_20200419_1840'),
    ]

    _VIEW_NAME = "passage_minute_view_v1"

    sql = f"""
CREATE VIEW {_VIEW_NAME} AS
SELECT 
    COUNT(id), 
    camera_id, 
    camera_naam, 
    date_trunc('minute', passage_at) as passage_at_minute 
FROM passage_passage 
GROUP BY 
    camera_id , 
    camera_naam,
    passage_at_minute 
ORDER BY passage_at_minute
;
"""

    reverse_sql = f"DROP VIEW IF EXISTS {_VIEW_NAME};"

    sql_materialized = f"""
    CREATE MATERIALIZED VIEW {_VIEW_NAME}_materialized AS
    SELECT * FROM {_VIEW_NAME};
    """

    reverse_sql_materialized = f"DROP MATERIALIZED VIEW IF EXISTS {_VIEW_NAME}_materialized;"

    operations = [
        migrations.RunSQL(
            sql=sql,
            reverse_sql=reverse_sql
        ),
        migrations.RunSQL(
            sql=sql_materialized,
            reverse_sql=reverse_sql_materialized
        ),
    ]
