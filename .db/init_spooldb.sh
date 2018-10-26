#!/bin/bash
set -e

SPOOL_USER=mysite_user
SPOOL_DB=mysite_db
SPOOL_PASSWORD=123
pass="PASSWORD '$SPOOL_PASSWORD'"
authMethod=md5

# SOURCE: https://github.com/aidanlister/postgres-hstore/blob/master/create_extension.sh
# Because both template1 and the user postgres database have already been created,
# we need to create the hstore extension in template1 and then recreate the postgres database.
#
# Running CREATE EXTENSION in both template1 and postgres can lead to
# the extensions having different eid's.
gosu postgres psql --dbname template1 <<EOSQL
	CREATE EXTENSION hstore;
	DROP DATABASE postgres;
	CREATE DATABASE postgres TEMPLATE template1;
EOSQL

gosu postgres psql <<EOSQL
	CREATE DATABASE "$SPOOL_DB" TEMPLATE template1;
EOSQL
echo

gosu postgres psql <<EOSQL
	CREATE USER "$SPOOL_USER" WITH CREATEDB $pass;
	GRANT ALL PRIVILEGES ON DATABASE "$SPOOL_DB" to "$SPOOL_USER";
EOSQL
echo

# leaving the line below in case it would be needed
# if it turns out to not be needed then it can, obviously, be removed
#{ echo; echo "host all all 0.0.0.0/0 $authMethod"; } >> "$PGDATA"/pg_hba.conf
