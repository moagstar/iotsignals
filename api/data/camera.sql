select
    straat,
    rijrichting,
    rijstrook,
    camera_id,
    camera_naam,
    camera_kijkrichting,
    camera_locatie,
    count(*)
from passage_passage_20210901
group by
    straat,
    rijrichting,
    rijstrook,
    camera_id,
    camera_naam,
    camera_kijkrichting,
    camera_locatie