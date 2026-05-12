"""ADMS push protocol helpers — parsing the ATTLOG body devices upload.

ZKTeco's push-firmware terminals POST to /iclock/cdata with tab-separated rows:

    <user_id>\t<timestamp>\t<status>\t<verify>\t<workcode>\t<reserved>

Timestamps are local "YYYY-MM-DD HH:MM:SS". We treat them as UTC for now —
timezone normalization belongs in a later feature once we model per-device tz.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class AdmsPunch:
    user_id: str
    timestamp: datetime
    status: int
    verify: int


def parse_attlog(body: str) -> list[AdmsPunch]:
    """Parse an ATTLOG payload. Skips malformed lines silently."""
    punches: list[AdmsPunch] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            ts = datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        except ValueError:
            continue
        punches.append(
            AdmsPunch(
                user_id=parts[0],
                timestamp=ts,
                status=int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                verify=int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
            )
        )
    return punches
