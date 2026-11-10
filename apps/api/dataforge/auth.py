"""Identity.

`dev` mode trusts the X-Dev-User header. It is for local work and CI only.
For a pilot, add a mode that verifies a token from a hosted provider and
returns its subject. The remaining code uses only `identity_subject`.
"""

import re

from fastapi import Header, HTTPException

from . import config

_SUBJECT = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")


def identity_subject(x_dev_user: str | None = Header(default=None)) -> str:
    if config.auth_mode() != "dev":
        raise HTTPException(501, "No identity provider is configured.")
    if not x_dev_user or not _SUBJECT.match(x_dev_user):
        raise HTTPException(401, "Send a valid X-Dev-User header.")
    return f"dev:{x_dev_user}"
