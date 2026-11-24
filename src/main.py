from contextlib import asynccontextmanager
from datetime import datetime

import aioboto3
import httpx
from fastapi import APIRouter, FastAPI, Path, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from furl import furl
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient

from minio import (
    find_free_id,
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


async def generate_screenshot(client, html: str) -> bytes:
    request = ScreenshotHTMLRequest(
        index_html=html,
        width=1000,
        format="png",
        wait_delay=5,
    )
    try:
        screenshot_bytes = await request.asend(client)
    except GotenbergServerError:
        screenshot_bytes = None
    return screenshot_bytes


async def load_site(client, minio, site_id: int) -> dict:
    request_time = datetime.now()
    bucket = minio.settings.minio.bucket
    endpoint = minio.settings.minio.endpoint

    url = f"{endpoint}/{bucket}/sites/{site_id}/index_{site_id}.html"
    download_url = make_download_url(url)

    title = await read_text_from_minio(client, bucket, f"{site_id}_title.txt")
    prompt = await read_text_from_minio(client, bucket, f"{site_id}_prompt.txt")
    screenshot_url = f"{endpoint}/{bucket}/sites/{site_id}/screenshot_{site_id}.png"

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
async def create_site(request: CreateSiteRequest, full_request: Request):
    request_time = datetime.now()
    state = full_request.app.state
    site_id = await find_free_id(state.minio_client, state.settings.minio.bucket)

    return {
        "id": site_id,
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
        title = generator.html_page.title
        screenshot = await generate_screenshot(gotenberg_client, generator.html_page.html_code)

        await upload_prompt_and_title(
            client,
            bucket,
            site_id,
            request_validated_data.prompt,
            title,
        )
        await upload_screenshot(client, site_id, screenshot)
        await upload_html(client, site_id, generator.html_page.html_code)

    return StreamingResponse(
        generate_and_upload(),
        media_type="text/html; charset=utf-8",
    )


@api_router.get("/sites/my", response_model=SitesListResponse)
async def show_my_sites(
    full_request: Request,
):
    state = full_request.app.state
    client = full_request.app.state.minio_client
    bucket = state.settings.minio.bucket
    response = await client.list_objects_v2(Bucket=bucket, Prefix="sites/")
    site_paths = response.get("Contents", [])
    site_ids = []
    sites = []

    for path in site_paths:
        site_id = path['Key']
        if not site_id.endswith(".html"):
            continue
        site_ids.append(int(furl(site_id).path.segments[1]))

    for site_id in site_ids:
        site = await load_site(client, state, site_id)
        sites.append(site)

    return {"sites": sites}


@api_router.get("/sites/{site_id}", response_model=SiteResponse)
async def site_response(
    full_request: Request,
    site_id: int = Path(..., gt=0, description="ID сайта"),
):
    state = full_request.app.state
    client = full_request.app.state.minio_client

    return await load_site(client, state, site_id)


app.include_router(api_router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
