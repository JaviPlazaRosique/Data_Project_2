CREATE USER usuario_datastream WITH REPLICATION IN ROLE cloudsqlsuperuser LOGIN PASSWORD '<contraseña usuario datastream (terraform)>';

GRANT CONNECT ON DATABASE "<nombre de la base de datos (terraform)>" TO usuario_datastream;

GRANT USAGE ON SCHEMA public TO usuario_datastream;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO usuario_datastream;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO usuario_datastream;

CREATE PUBLICATION datastream_publication FOR ALL TABLES;

SELECT pg_create_logical_replication_slot('datastream_slot', 'pgoutput');