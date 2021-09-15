select
    case kenteken_land when null then null else md5(kenteken_land) end as kenteken_land,
    case voertuig_soort when null then null else md5(voertuig_soort) end as voertuig_soort,
    case merk when null then null else md5(merk) end as merk,
    case inrichting when null then null else md5(inrichting) end as inrichting,
    datum_eerste_toelating,
    NULL,  -- datum_tenaamstelling
    case toegestane_maximum_massa_voertuig when null then null else md5(toegestane_maximum_massa_voertuig) end as toegestane_maximum_massa_voertuig,
    case europese_voertuigcategorie when null then null else md5(europese_voertuigcategorie) end as europese_voertuigcategorie,
    case europese_voertuigcategorie_toevoeging when null then null else md5(europese_voertuigcategorie_toevoeging) end as europese_voertuigcategorie_toevoeging,
    case when taxi_indicator then 'TRUE' else 'FALSE' end as taxi_indicator,
    maximale_constructie_snelheid_bromsnorfiets,
    brandstoffen,
    extra_data,
    diesel,
    gasoline,
    electric,
    case versit_klasse when null then null else md5(versit_klasse) end as versit_klasse,
    count(*)
from passage_passage_20210901
group by
    kenteken_land,
    voertuig_soort,
    merk,
    inrichting,
    datum_eerste_toelating,
    NULL,  -- datum_tenaamstelling
    toegestane_maximum_massa_voertuig,
    europese_voertuigcategorie,
    europese_voertuigcategorie_toevoeging,
    taxi_indicator,
    maximale_constructie_snelheid_bromsnorfiets,
    brandstoffen,
    extra_data,
    diesel,
    gasoline,
    electric,
    versit_klasse