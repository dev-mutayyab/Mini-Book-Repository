from typing import Dict, Any
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class LoginResponse(BaseModel):
    message: str
    status: int
    data: TokenResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str
    new_password: str


class OTPRequest(BaseModel):
    otp: int


class GenericSuccess(BaseModel):
    message: str
    status: int
    data: Dict[str, Any]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, example="NewSecurePass123")


class AzureAdLoginRequest(BaseModel):
    token: str
