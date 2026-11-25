from furl import furl


def make_download_url(url: str) -> str:
    url = furl(url)
    url.args["response-content-disposition"] = "attachment"
    return url.url


async def upload_html(client, bucket: str, site_id: int, html: str) -> None:
    await client.put_object(
        Bucket=bucket,
        Key=f"sites/{site_id}/index_{site_id}.html",
        Body=html.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )


async def upload_screenshot(client, bucket: str, site_id: int, screenshot: bytes, screenshot_format: str) -> None:
    await client.put_object(
        Bucket=bucket,
        Key=f"sites/{site_id}/screenshot_{site_id}.{screenshot_format}",
        Body=screenshot,
        ContentType=f"image/{screenshot_format}",
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


async def read_text_from_minio(client, bucket: str, key: str) -> str:
    response = await client.get_object(Bucket=bucket, Key=key)
    body = response["Body"]

    async with body:
        content = await body.read()

    return content.decode("utf-8")
