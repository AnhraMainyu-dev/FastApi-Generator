from botocore.exceptions import ClientError
from furl import furl


def make_download_url(url: str) -> str:
    url = furl(url)
    url.args["response-content-disposition"] = "attachment"
    return url.url


async def upload_html(client, site_id: int, html: str) -> None:
    await client.put_object(
        Bucket="generated-sites",
        Key=f"sites/{site_id}/index_{site_id}.html",
        Body=html.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )


async def upload_screenshot(client, site_id: int, screenshot: bytes) -> None:
    await client.put_object(
        Bucket="generated-sites",
        Key=f"sites/{site_id}/screenshot_{site_id}.png",
        Body=screenshot,
        ContentType="image/png",
        ContentDisposition="inline",
    )


async def upload_prompt_and_title(client, bucket: str, site_id: int, prompt: str, title: str) -> None:
    await client.put_object(
        Bucket=bucket,
        Key=f"{site_id}_prompt.txt",
        Body=prompt.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )
    await client.put_object(
        Bucket=bucket,
        Key=f"{site_id}_title.txt",
        Body=title.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )


async def write_site_id(client, bucket: str, next_id: int, etag: str) -> None:
    await client.put_object(
        Bucket=bucket,
        Key="last-id.txt",
        Body=str(next_id).encode("utf-8"),
        IfMatch=etag,
    )


async def get_last_id(client, bucket: str, key: str) -> tuple[int, str]:
    response = await client.get_object(Bucket=bucket, Key=key)
    body = response['Body']

    async with body:
        last_id = int(await body.read())

    return last_id, response["ETag"]


async def find_free_id(client, bucket: str) -> int:
    for _ in range(10):
        last_id, etag = await get_last_id(client, bucket, "last-id.txt")
        next_id = last_id + 1

        try:
            await write_site_id(client, bucket, next_id, etag)
        except ClientError:
            continue

        return next_id

    raise RuntimeError("Не получилось индексировать сайт")


async def read_text_from_minio(client, bucket: str, key: str) -> str:
    response = await client.get_object(Bucket=bucket, Key=key)
    body = response["Body"]

    async with body:
        content = await body.read()

    return content.decode("utf-8")


async def get_screenshot_from_minio(client, bucket: str, key: str) -> str:
    response = await client.get_object(Bucket=bucket, Key=key)
    body = response["Body"]

    async with body:
        content = await body.read()

    return content
