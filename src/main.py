from contextlib import asynccontextmanager
from datetime import datetime

import aioboto3
import httpx
from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient

from minio import (
    make_download_url,
    read_text_from_minio,
    upload_html,
    upload_prompt_and_title,
    upload_screenshot,
)
from models import CreateSiteRequest, SiteGenerationRequest, SiteResponse, SitesListResponse, UserProfile
from settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    minio = settings.minio
    session = aioboto3.Session()

    async with (
        AsyncDeepseekClient.setup(
            settings.deepseek.api_key,
            limits=httpx.Limits(max_connections=settings.deepseek.max_connections),
        ),
        AsyncUnsplashClient.setup(
            settings.unsplash.api_key,
            timeout=settings.unsplash.timeout,
            limits=httpx.Limits(max_connections=settings.unsplash.max_connections),
        ),
        session.client(
            service_name="s3",
            endpoint_url=minio.endpoint,
            aws_access_key_id=minio.access_key.get_secret_value(),
            aws_secret_access_key=minio.secret_key.get_secret_value(),
            region_name=minio.region_name,
        ) as minio_client,
        httpx.AsyncClient(
            base_url=settings.gotenberg.base_url,
            timeout=settings.gotenberg.timeout,
        ) as gotenberg_client,
    ):
        app.state.minio_client = minio_client
        app.state.gotenberg_client = gotenberg_client
        yield


api_router = APIRouter(prefix="/frontend-api")
app = FastAPI(lifespan=lifespan)


async def generate_screenshot(client, html: str, width: int, screenshot_format: str, wait_delay: int) -> bytes:
    request = ScreenshotHTMLRequest(
        index_html=html,
        width=width,
        format=screenshot_format,
        wait_delay=wait_delay,
    )
    try:
        screenshot_bytes = await request.asend(client)
    except GotenbergServerError:
        screenshot_bytes = None
    return screenshot_bytes


mock_user = {
    "email": "example@example.com",
    "isActive": True,
    "profileId": "1",
    "registeredAt": "2025-06-15T18:29:56+00:00",
    "updatedAt": "2025-06-15T18:29:56+00:00",
    "username": "user124",
    "trash_info": "secret_code",
}


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
    request_validated_data: SiteGenerationRequest,
    full_request: Request,
    site_id: int = Path(..., gt=0, description="ID сайта"),
):
    generator = AsyncPageGenerator(debug_mode=full_request.app.state.settings.debug)
    client = full_request.app.state.minio_client
    gotenberg_client = full_request.app.state.gotenberg_client

    async def generate_and_upload():
        async for chunk in generator(request_validated_data.prompt):
            yield chunk

        bucket = full_request.app.state.settings.minio.bucket
        gotenberg = full_request.app.state.settings.gotenberg
        screenshot_format = gotenberg.screenshot_format
        title = generator.html_page.title
        screenshot = await generate_screenshot(
            gotenberg_client,
            generator.html_page.html_code,
            gotenberg.screenshot_width,
            screenshot_format,
            gotenberg.wait_delay,
        )

        await upload_prompt_and_title(
            client,
            bucket,
            site_id,
            request_validated_data.prompt,
            title,
        )
        if screenshot is not None:
            await upload_screenshot(client, bucket, site_id, screenshot, screenshot_format)
        await upload_html(client, bucket, site_id, generator.html_page.html_code)

    return StreamingResponse(
        generate_and_upload(),
        media_type="text/html; charset=utf-8",
    )


@api_router.get("/sites/my", response_model=SitesListResponse)
async def show_my_sites(
    full_request: Request,
):
    site = await site_response(full_request, 1)
    return {"sites": [site]}


@api_router.get("/sites/{site_id}", response_model=SiteResponse)
async def site_response(
    full_request: Request,
    site_id: int = Path(..., gt=0, description="ID сайта"),
):
    state = full_request.app.state
    client = full_request.app.state.minio_client

    request_time = datetime.now()
    bucket = state.settings.minio.bucket
    endpoint = state.settings.minio.endpoint

    url = f"{endpoint}/{bucket}/sites/{site_id}/index_{site_id}.html"
    download_url = make_download_url(url)

    title = await read_text_from_minio(client, bucket, f"{site_id}_title.txt")
    prompt = await read_text_from_minio(client, bucket, f"{site_id}_prompt.txt")
    screenshot_format = state.settings.gotenberg.screenshot_format
    screenshot_url = f"{endpoint}/{bucket}/sites/{site_id}/screenshot_{site_id}.{screenshot_format}"

    return {
        "id": site_id,
        "title": title,
        "prompt": prompt,
        "htmlCodeUrl": url,
        "htmlCodeDownloadUrl": download_url,
        "screenshotUrl": screenshot_url,
        "createdAt": request_time,
        "updatedAt": request_time,
    }


app.include_router(api_router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
