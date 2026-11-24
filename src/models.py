from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

SiteTitle = Annotated[str, Field(min_length=3, max_length=100, description="Название сайта")]


class UserProfile(BaseModel):
    username: str = Field(..., description="Юзернейм")
    updatedAt: datetime = Field(..., description="Дата обновления")
    registeredAt: datetime = Field(..., description="Дата регистрации")
    profileId: str = Field(..., description="ID профиля")
    email: str = Field(..., description="Электронный адрес")
    isActive: bool = Field(..., description="Статус")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "example@example.com",
                    "isActive": True,
                    "profileId": "1",
                    "registeredAt": "2025-06-15T18:29:56+00:00",
                    "updatedAt": "2025-06-15T18:29:56+00:00",
                    "username": "user125",
                },
            ],
        },
    )


class CreateSiteRequest(BaseModel):
    title: SiteTitle | None = Field(None, description="Название сайта")
    prompt: str = Field(..., description="Промт для генерации сайта")


class SiteGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Промт для генерации сайта")


class SiteResponse(BaseModel):
    id: int
    title: SiteTitle
    htmlCodeUrl: str | None
    htmlCodeDownloadUrl: str | None
    screenshotUrl: str | None
    prompt: str
    createdAt: datetime
    updatedAt: datetime


class SitesListResponse(BaseModel):
    sites: list[SiteResponse]
