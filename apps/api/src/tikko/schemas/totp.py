"""TOTP request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

# RFC 6238 codes are 6 digits.
_CODE_PATTERN = r"^\d{6}$"


class TOTPEnrollResponse(BaseModel):
    secret: str
    otpauth_uri: str
    enabled: bool


class TOTPVerifyRequest(BaseModel):
    code: str = Field(..., pattern=_CODE_PATTERN)


class TOTPVerifyResponse(BaseModel):
    enabled: bool
    # Plaintext codes returned **once** at verify time. The server stores only
    # SHA-256 hashes; the user must save these somewhere safe.
    recovery_codes: list[str]


class TOTPDisableRequest(BaseModel):
    password: str


class TOTPRecoveryCodesRegenerateRequest(BaseModel):
    password: str


class TOTPRecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
