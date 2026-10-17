# Relational database and SQL queries

A relational database for anime studios, creators and releases, with seven queries ranging from simple joins to relational division and quantified comparisons. Originally built on the university's MariaDB server; here it runs locally in DuckDB with no server needed.

## Run it

```bash
pip install duckdb
python run_queries.py
```

The script builds the schema, loads the sample data, runs every query and checks each result against an answer worked out by hand from the data. Expected output ends with `7/7 queries returned the expected result.`

## Files

| File | Contents |
|---|---|
| `schema.sql` | Six tables with primary and foreign keys: `Creator`, `Studio`, `Anime`, and the link tables `ContractsWith`, `CreatedBy` and `Releases` |
| `queries.sql` | The seven queries, each with a one-line description |
| `seed.sql` | Invented sample data, designed so that every query has a non-trivial answer |
| `run_queries.py` | Builds the database in memory, runs the queries and checks the results |

## What the queries cover

| Query | Technique |
|---|---|
| Q1 Studios that released a TV anime | Multi-table join, `DISTINCT` |
| Q2 Studios releasing both mecha and slice-of-life | Self-join on `Releases` |
| Q3 Studios releasing every isekai title with stock | Relational division with `GROUP BY ... HAVING COUNT` against a subquery |
| Q4 Slice-of-life studios with no creator over 30 | `NOT IN` anti-join |
| Q5 Oldest contracted creator per studio | Aggregation with `MAX` |
| Q6 Creators older than any 'Mecha Forge' creator | Quantified comparison with `> ANY` |
| Q7 Creators at studios spanning five or more genres | `IN` subquery with `HAVING COUNT(DISTINCT ...)` |
