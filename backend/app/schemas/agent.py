import uuid

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AgentRegister(BaseModel):
    agent_name: str = Field(min_length=2, max_length=150)
    company_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    industry: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10, max_length=3000)

    interests: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    excluded_industries: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    company_name: str
    email: EmailStr
    industry: str
    description: str
    interests: list[str]
    capabilities: list[str]
    excluded_industries: list[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"