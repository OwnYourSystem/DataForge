import pytest

from dataforge.guard import GuardError, check_learner_sql

S = "{{ source('retail_raw', 'raw_customers') }}"
DIALECTS = ["duckdb", "databricks"]

OK = [
    "select 1",
    f"select * from {S}",
    'select * from {{ref("stg_customers")}} -- comment',
    f"select no_such_column from {S}",
    "select * from (values (cast(1 as bigint), 'a', current_timestamp)) t(k, n, p)",
    f"select a.customer_id from {S} a join {S} b on a.customer_id = b.customer_id",
    f"with x as (select * from {S}), y as (select * from x) "
    "select row_number() over (order by customer_id) rn, * from y union all select 1, * from x",
    f"select customer_id, (select count(*) from {S}) n from {S}",
    f"select cast(customer_id as bigint), trim(customer_name), lower(email) from {S}",
]
BAD_JINJA = [
    "select '{{ env_var('DBX_TOKEN') }}' as t",
    "select {{ env_var('PATH') }}",
    "{% set x = run_query('select 1') %} select 1",
    "{% macro m() %}{% endmacro %}",
    "select {{ source('a','b') ~ env_var('X') }}",
    "select {{ var('x') }}",
    "select {{ config(post_hook='drop table x') }}",
    "{{ source('a', 'b') }} {{ modules.os.environ }}",
    "select {# hidden #} 1",
    "select {{ source('a','b') }",
    "select 1 }}",
    "select '" + "x" * 30_000 + "'",
]
BAD_SQL = [
    # Reads that do not go through source() or ref()
    "select * from raw_customers",
    "select * from main.raw_customers",
    "select * from other_cat.df_run_abc.stg_customers",
    "select * from system.information_schema.tables",
    "select * from information_schema.schemata",
    "select * from df_relation_0",
    "select * from delta.`/mnt/x`",
    "select * from csv.`s3://bucket/x`",
    "select * from identifier('a.b.c')",
    # Table functions and functions that reach outside the query
    "select * from read_text('/etc/hostname')",
    f"select content from {S}, read_text('/etc/hostname')",
    "select * from read_files('/Volumes/x')",
    "select * from range(10)",
    "select * from query('select 1')",
    "select secret('scope', 'key') as x",
    "select getenv('HOME')",
    "select ai_query('model', 'hi')",
    "select http_request(conn => 'x')",
    "select reflect('java.lang.System', 'getenv', 'X')",
    # More than one statement, or not a query
    f"select * from {S}; drop table x",
    f"select 1 as a); set enable_external_access=true; create table x as (select 1 from {S}",
    "drop table x",
    "create table x as select 1",
    "set x = 1",
    "attach 'x.db'",
    "copy (select 1) to 'x.csv'",
    "show schemas",
    "describe table x",
    "select 1 from",
    "",
]


@pytest.mark.parametrize("dialect", DIALECTS)
@pytest.mark.parametrize("sql", OK)
def test_approved_sql_passes(sql, dialect):
    check_learner_sql(sql, dialect)


@pytest.mark.parametrize("dialect", DIALECTS)
@pytest.mark.parametrize("sql", BAD_JINJA + BAD_SQL)
def test_unapproved_sql_is_rejected(sql, dialect):
    with pytest.raises(GuardError):
        check_learner_sql(sql, dialect)


def test_lesson_files_pass_the_guard(lessons):
    lesson = lessons["lab-001"]
    model = "models/staging/stg_customers.sql"
    for dialect in DIALECTS:
        check_learner_sql(lesson.starter_files()[model], dialect)
        check_learner_sql((lesson.root / "solution" / model).read_text(), dialect)
