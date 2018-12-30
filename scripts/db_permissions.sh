#!/usr/bin/env bash

export user=$USER
export dbs=$USER

for db in $dbs; do
    psql -c "alter database $db owner to $user" $db;
done

for db in $dbs; do
    psql -c "alter schema public owner to $user" $db;
done

for db in $dbs; do
    tables=`psql -qAt -c "select tablename from pg_tables where schemaname = 'public';" $db`

    for tbl in $tables; do
        psql -c "alter table \"$tbl\" owner to $user" $db;
    done;
done

for db in $dbs; do
    seqs=`psql -qAt -c "select sequence_name from information_schema.sequences where sequence_schema = 'public';" $db`

    for seq in $seqs; do
        psql -c "alter table \"$seq\" owner to $user" $db ;
    done;
done

for db in $dbs; do
    views=`psql -qAt -c "select table_name from information_schema.views where table_schema = 'public';" $db`

    for view in $views; do
        psql -c "alter table \"$view\" owner to $user" $db ;
    done;
done

exit
