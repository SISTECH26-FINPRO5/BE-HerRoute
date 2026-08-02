from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

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

class RiskIndicatorRequest(BaseModel):
    lat: float
    lon: float
    dow: int = Field(description="Day of week (0=Monday, 6=Sunday)")
    hour: int = Field(description="Hour of day (0-23)")

class RiskIndicatorResponse(BaseModel):
    cell_id: str
    risk_score: float
    tier: str
    color: str
    is_mock: bool
    mock_note: str

class SafePlaceResponse(BaseModel):
    name: str
    amenity_type: str
    lat: float
    lon: float
    is_mock: bool

class SafeRouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    mode: str = Field("safe", description="Mode of routing: 'safe' or 'fast'")

class SafeRouteResponse(BaseModel):
    path: List[str]
    avg_risk: float
    is_mock: bool
    mock_note: str

class ReportCreate(BaseModel):
    lat: float
    lon: float
    category: str
    description: str

class ReportResponse(BaseModel):
    id: int
    lat: float
    lon: float
    category: str
    description: str
    created_at: str
