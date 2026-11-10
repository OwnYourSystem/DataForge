import pytest

from dataforge.guard import GuardError, check_learner_sql

OK = [
    "select 1",
    "select * from {{ source('retail_raw', 'raw_customers') }}",
    'select * from {{ref("stg_customers")}} -- comment',
]
BAD = [
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


@pytest.mark.parametrize("sql", OK)
def test_approved_sql_passes(sql):
    check_learner_sql(sql)


@pytest.mark.parametrize("sql", BAD)
def test_unapproved_jinja_is_rejected(sql):
    with pytest.raises(GuardError):
        check_learner_sql(sql)
