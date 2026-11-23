import asyncio

from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient

from settings import Settings


async def main():
    settings = Settings()

    async with (
        AsyncUnsplashClient.setup(settings.unsplash.api_key, timeout=settings.unsplash.timeout),
        AsyncDeepseekClient.setup(
            settings.deepseek.api_key,
        ),
    ):
        generator = AsyncPageGenerator(debug_mode=settings.debug)
        async for chunk in generator("Сайт кофейни в готическом стиле"):
            print(chunk, end="", flush=True)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(generator.html_page.html_code)

        print("Файл успешно сохранён!")


asyncio.run(main())
