"""Password recovery API schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, SecretStr


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: SecretStr
    new_password: SecretStr


class PasswordResetResponse(BaseModel):
    message: str



class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
