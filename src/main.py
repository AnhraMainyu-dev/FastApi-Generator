import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, FastAPI, Path
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

api_router = APIRouter(prefix="/frontend-api")
app = FastAPI()

SiteTitle = Annotated[str, Field(min_length=3, max_length=100, description="Название сайта")]


async def generate_html(chunk_size: int = 200):
    with open("static/mock.html", encoding="utf-8") as f:
        html = f.read()
    for i in range(0, len(html), chunk_size):
        yield html[i : (i + chunk_size)]
        await asyncio.sleep(0.1)


class UserProfile(BaseModel):
    username: str = Field(..., description="Юзернейм")
    updatedAt: datetime = Field(..., description="Дата обновление")
    registeredAt: datetime = Field(..., description="Дата регистрации")
    profileId: str = Field(..., description="ID профиля")
    email: str = Field(..., description="Электронный адрес")
    isActive: bool = Field(..., description="Статус")

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "email": "example@example.com",
            "isActive": True,
            "profileId": "1",
            "registeredAt": "2025-06-15T18:29:56+00:00",
            "updatedAt": "2025-06-15T18:29:56+00:00",
            "username": "user125",
        }],
    })


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


mock_user = {
    "email": "example@example.com",
    "isActive": True,
    "profileId": "1",
    "registeredAt": "2025-06-15T18:29:56+00:00",
    "updatedAt": "2025-06-15T18:29:56+00:00",
    "username": "user124",
    "trash_info": "secret_code",
    }


@api_router.get("/hello")
async def hello():
    return {"message": "Привет из бекенда!"}


@api_router.get("/users/me")
async def info():
    profile = UserProfile(**mock_user)
    return profile


@api_router.post("/sites/create", response_model=SiteResponse)
async def create_site(request: CreateSiteRequest):
    request_time = datetime.now()
    return {
        "id": 1,
        "title": request.title or "Новый сайт",
        "urlPath": "",
        "prompt": request.prompt,
        "htmlCodeUrl": None,
        "htmlCodeDownloadUrl": None,
        "screenshotUrl": None,
        "createdAt": request_time,
        "updatedAt": request_time,
    }


@api_router.post("/sites/{site_id}/generate")
async def generate_site(
    request: SiteGenerationRequest,
    site_id: int = Path(..., gt=0, description="ID сайта"),
):
    return StreamingResponse(
        generate_html(),
        media_type="text/html; charset=utf-8",
    )


@api_router.get("/sites/my", response_model=SitesListResponse)
async def show_my_sites():
    request_time = datetime.now()
    return {
        "sites": [
            {
                "id": 1,
                "title": "Сайт про стегозавров",
                "prompt": "Сайт про стегозавров",
                "htmlCodeUrl": "/mock.html",
                "htmlCodeDownloadUrl": "/mock.html",
                "screenshotUrl": None,
                "createdAt": request_time,
                "updatedAt": request_time,
            },
            {
                "id": 2,
                "title": "Сайт про стегозавров",
                "prompt": "Сайт про стегозавров",
                "htmlCodeUrl": "/mock.html",
                "htmlCodeDownloadUrl": "/mock.html",
                "screenshotUrl": None,
                "createdAt": request_time,
                "updatedAt": request_time,
            },
        ],
    }


@api_router.get("/sites/{site_id}", response_model=SiteResponse)
async def site_response(
    site_id: int = Path(..., gt=0, description="ID сайта"),
):
    request_time = datetime.now()
    return {
        "id": site_id,
        "title": "Заглушка",
        "prompt": "Заглушка",
        "htmlCodeUrl": "/mock.html",
        "htmlCodeDownloadUrl": "/mock.html",
        "screenshotUrl": None,
        "createdAt": request_time,
        "updatedAt": request_time,
    }


app.include_router(api_router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
