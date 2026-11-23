# FastAI

Сервис для генерации HTML-сайтов по текстовому описанию с помощью DeepSeek. Для подбора изображений используется Unsplash.

## Как запустить dev-версию

Установите [uv](https://docs.astral.sh/uv/) и выполните:

```sh
uv sync
```

Скопируйте `example.env` в `.env`, укажите ключ DeepSeek и Access Key Unsplash. Для `MAX_CONNECTIONS` укажите `5`, для `TIMEOUT` — `20`.

Запустите сервер:

```sh
uv run fastapi dev src/main.py
```


