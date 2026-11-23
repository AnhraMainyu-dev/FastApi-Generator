import asyncio

import aioboto3
from furl import furl

from settings import Settings


def make_download_url(url: str) -> str:
    url = furl(url)
    url.args["response-content-disposition"] = "attachment"
    return url.url


download_url = make_download_url("http://192.168.0.74:9000/generated-sites/index.html")


async def upload_file():
    settings = Settings()
    session = aioboto3.Session()

    with open("index.html", "rb") as file:
        image_data = file.read()

    async with session.client(
        service_name="s3",
        endpoint_url=settings.minio.endpoint,
        aws_access_key_id=settings.minio.access_key.get_secret_value(),
        aws_secret_access_key=settings.minio.secret_key.get_secret_value(),
        region_name=settings.minio.region_name,
    ) as client:
        await client.put_object(
            Bucket="generated-sites",
            Key="index.html",
            Body=image_data,
            ContentType="text/html",
            ContentDisposition="inline",
        )


if __name__ == "__main__":
    asyncio.run(upload_file())
