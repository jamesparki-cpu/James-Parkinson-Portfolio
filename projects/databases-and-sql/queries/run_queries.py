"""Build the anime studio database in memory, run every query, and check the answers.

Usage:
    pip install duckdb
    python run_queries.py

DuckDB is used so the project runs with no database server. The SQL itself is
standard and was originally written for MariaDB.
"""
from pathlib import Path

import duckdb

HERE = Path(__file__).parent

# Answers worked out by hand from seed.sql; each query is checked against them.
EXPECTED = {
    "Q1": {("Mecha Forge",), ("Sunlit Frames",), ("Portal Works",)},
    "Q2": {("Mecha Forge",), ("Portal Works",)},
    "Q3": {("Portal Works",)},
    "Q4": {(4,)},
    "Q5": {(1, 41), (2, 35), (3, 31), (4, 24)},
    "Q6": {("Kenji Mori",), ("Lena Fischer",), ("Mina Park",)},
    "Q7": {("Mina Park",), ("Sam Okafor",)},
}


def split_queries(sql: str) -> list[tuple[str, str]]:
    """Split queries.sql into (title, statement) pairs using the '-- Qn.' comments."""
    out, title, buf = [], None, []
    for line in sql.splitlines():
        if line.startswith("-- Q"):
            if title:
                out.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        elif title and not line.startswith("--"):
            buf.append(line)
    if title:
        out.append((title, "\n".join(buf).strip()))
    return out


def main() -> None:
    con = duckdb.connect()
    con.execute((HERE / "schema.sql").read_text())
    con.execute((HERE / "seed.sql").read_text())

    failures = 0
    for title, stmt in split_queries((HERE / "queries.sql").read_text()):
        key = title.split(".")[0]
        cur = con.execute(stmt.rstrip(";"))
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        ok = set(rows) == EXPECTED[key]
        failures += not ok
        print(f"\n{'PASS' if ok else 'FAIL'}  {title}")
        print("   " + " | ".join(cols))
        for row in sorted(rows):
            print("   " + " | ".join(str(v) for v in row))

    print(f"\n{len(EXPECTED) - failures}/{len(EXPECTED)} queries returned the expected result.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
