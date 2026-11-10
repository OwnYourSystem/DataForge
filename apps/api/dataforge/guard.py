"""Checks on learner SQL before it goes to dbt.

dbt renders Jinja in model files. Jinja can read environment variables and
run macros, so the learner gets only `source()` and `ref()`.
"""

import re

MAX_FILE_BYTES = 20_000

_ALLOWED_EXPRESSION = re.compile(
    r"""^\s*(
        source\(\s*(['"])[A-Za-z0-9_]+\2\s*,\s*(['"])[A-Za-z0-9_]+\3\s*\)
        |
        ref\(\s*(['"])[A-Za-z0-9_]+\4\s*\)
    )\s*$""",
    re.VERBOSE,
)
_EXPRESSION = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)


class GuardError(ValueError):
    pass


def check_learner_sql(content: str) -> None:
    """Raise GuardError if the file has Jinja that is not approved."""
    if len(content.encode()) > MAX_FILE_BYTES:
        raise GuardError(f"The file is larger than {MAX_FILE_BYTES} bytes.")
    if "\x00" in content:
        raise GuardError("The file contains a NUL character.")
    if "{%" in content or "%}" in content:
        raise GuardError("Jinja blocks ({% ... %}) are not permitted.")
    if "{#" in content or "#}" in content:
        raise GuardError("Jinja comments ({# ... #}) are not permitted. Use SQL comments.")
    for match in _EXPRESSION.finditer(content):
        if not _ALLOWED_EXPRESSION.match(match.group(1)):
            raise GuardError(
                "Only {{ source('name', 'table') }} and {{ ref('model') }} are permitted. "
                f"Found: {{{{{match.group(1)}}}}}"
            )
    remainder = _EXPRESSION.sub("", content)
    if "{{" in remainder or "}}" in remainder:
        raise GuardError("A Jinja expression is not closed correctly.")
