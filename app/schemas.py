from pydantic import BaseModel, Field

# Simple regex that ensures there is an '@' and a '.'
EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

class UserCreate(BaseModel):
    full_name: str = Field(json_schema_extra={"example": "String"})
    email: str = Field(pattern=EMAIL_REGEX, json_schema_extra={"example": "string@example.com"})
    password: str = Field(json_schema_extra={"example": "string"})

class UserLogin(BaseModel):
    email: str = Field(pattern=EMAIL_REGEX, json_schema_extra={"example": "string@example.com"})
    password: str = Field(json_schema_extra={"example": "string"})

class TrustedContactCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Mom"})
    phone_number: str = Field(..., json_schema_extra={"example": "+628123456789"})
