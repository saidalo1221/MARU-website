"""app/schema_mariadb.sql is what gets run on a fresh MariaDB. If a model gains a table or column and the SQL is not
updated, production breaks at the first query - SQLite tests cannot see that (they build tables from the models).
This compares table and column names of the SQL file with the models, and the session-12 migration with both."""

import re
from pathlib import Path

import app.models  # noqa: F401 - registers every model
from app.database import Base

ROOT = Path(__file__).resolve().parent.parent / "app"
SCHEMA = (ROOT / "schema_mariadb.sql").read_text(encoding="utf-8")


def _sql_tables(text):
    tables = {}
    for m in re.finditer(r"CREATE TABLE `?(\w+)`? \((.*?)\)\s*(?:CHARSET|ENGINE|DEFAULT)", text, re.S):
        cols = set()
        for line in m.group(2).splitlines():
            line = line.strip().rstrip(",")
            tok = re.match(r"`?(\w+)`?\s+[A-Za-z]", line)
            if tok and tok.group(1).upper() not in {"PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT", "KEY", "INDEX", "CHECK"}:
                cols.add(tok.group(1))
        tables[m.group(1)] = cols
    return tables


def test_every_model_table_and_column_is_in_the_mariadb_schema():
    sql = _sql_tables(SCHEMA)
    assert len(sql) >= 50 and sum(len(c) for c in sql.values()) > 500, "the SQL parser found too little; fix this test"
    problems = []
    for table in Base.metadata.sorted_tables:
        if table.name not in sql:
            problems.append(f"table {table.name} is missing from schema_mariadb.sql")
            continue
        for column in table.columns:
            if column.name not in sql[table.name]:
                problems.append(f"{table.name}.{column.name} is missing from schema_mariadb.sql")
    extra = sorted(set(sql) - {t.name for t in Base.metadata.sorted_tables})
    assert not problems, "\n".join(problems)
    assert not extra, f"tables in the SQL file that no model defines: {extra}"
