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


class TOTPDisableRequest(BaseModel):
    password: str
