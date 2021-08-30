--
-- Request: export van de data van ANPR Camera 1007 op de Jan van Galenstraat.
-- Start: 1 mei
-- Einde: nu
-- Camera id: 5274d916-0cf3-4cfe-abe7-63005aeec49d
-- Velden:
--     id
--     passage_at
--     created_at
--     version
--     straat
--     rijrichting
--     rijstrook
--     camera_id
--     camera_naam
--     camera_kijkrichting
--     camera_locatie
--     kenteken_land
--     kenteken_nummer_betrouwbaarheid
--     kenteken_land_betrouwbaarheid
--     kenteken_karakters_betrouwbaarheid
--     automatisch_verwerkbaar
--     voertuig_soort
--     inrichting
--     toegestane_maximum_massa_voertuig
--     europese_voertuigcategorie
--     europese_voertuigcategorie_toevoeging
--     brandstoffen
--     extra_data
--     diesel
--     gasoline
--     electric
--     indicatie_snelheid
--
-- Werkwijze:
-- - Op acc test draaien met subset van de partities (table_name = 'passage_passage_20210701')
-- - Valideren dat data klopt
-- - Volledige query op prod draaien
-- - CSV's naar tar.gz, versturen via DocZend


DO LANGUAGE plpgsql
    $$
    DECLARE
        passage_partition record;
    BEGIN
        FOR passage_partition IN
            SELECT table_name
            FROM information_schema.tables
            WHERE
                table_schema = 'public'
                AND (table_name LIKE 'passage_passage_202105%'
                OR table_name LIKE 'passage_passage_202106%'
                OR table_name LIKE 'passage_passage_202107%')
            ORDER BY table_name
        LOOP
            EXECUTE format('COPY (SELECT id, passage_at, created_at, version, straat, rijrichting, rijstrook, camera_id, camera_naam, camera_kijkrichting, camera_locatie, kenteken_land, kenteken_nummer_betrouwbaarheid, kenteken_land_betrouwbaarheid, kenteken_karakters_betrouwbaarheid, automatisch_verwerkbaar, voertuig_soort, inrichting, toegestane_maximum_massa_voertuig, europese_voertuigcategorie, europese_voertuigcategorie_toevoeging, brandstoffen, extra_data, diesel, gasoline, electric, indicatie_snelheid FROM %I WHERE camera_id = %L OR camera_id = %L) TO %L DELIMITER %L CSV;',
            passage_partition.table_name,
            '89641b49-fe43-4094-96bc-99b5971f167e',
            '07b48bc1-f42b-42e1-92de-b21ec9f1d249',
            '/tmp/zwaar_verkeer/data_export_' || passage_partition.table_name || '.csv',
            ';');
        END LOOP;
    END;
$$;