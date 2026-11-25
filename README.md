# FastAI

FastAI предназначен для генерации HTML-страничек для сервисов по их описанию с помощью DeepSeek. Сервис поддерживает хранение 
сгенерированных сайтов в MinIO.

## Сторонние сервисы

Для работы FastAI требуется зарегистрировать в сервисе [Unsplash](unsplash.com) и получить API-ключ.
Точно также для работы требуется API-ключ сервиса DeepSeek с доступными кредитами для использования

## Как запустить dev-версию на Windows

Установите git, uv и сервис MinIO AIStor.

В PowerShell из корня проекта выполните:

```powershell
uv sync --locked --python 3.13
.\.venv\Scripts\Activate.ps1
```

`uv sync` создаёт окружение `.venv` и устанавливает зависимости из `uv.lock`. 
Проверено на версии Python 3.13


### Настройте `.env`

Создайте и заполните `.env` в корне проекта по примеру env.example. 

```dotenv
DEBUG=False 

DEEPSEEK__API_KEY=[API-ключ дипсика]
DEEPSEEK__MAX_CONNECTIONS=[Максимальное количество подключений одновременно]

UNSPLASH__API_KEY=[Access-ключ дипсика]
UNSPLASH__MAX_CONNECTIONS=[Максимальное количество подключений одновременно]
UNSPLASH__TIMEOUT=[Максимальное время ожидания ответа от сервиса]

MINIO__ENDPOINT=http://127.0.0.1:9000
MINIO__ACCESS_KEY=[Идентификатор ключа доступа, он же логин для авторизации]
MINIO__SECRET_KEY=[Секретный ключ доступа, он же пароль для авторизации]
MINIO__REGION_NAME=[Имя региона, которое клиент использует при подписи запросов]
MINIO__BUCKET=[Имя bucket-а в сервисе]
MINIO__TIMEOUT=[Максимальное время ожидания ответа от сервиса]
MINIO__READING_TIMEOUT=[Максимальное время чтения ответа от сервиса]
MINIO__MAX_CONNECTIONS=[Максимальное количество подключений одновременно]

GOTENBERG__BASE_URL=https://demo.gotenberg.dev
GOTENBERG__SCREENSHOT_WIDTH=[Ширина изображения в пикселях]
GOTENBERG__SCREENSHOT_FORMAT=[Расширение изображения]
GOTENBERG__WAIT_DELAY=[Задержка перед созданием скриншота]
GOTENBERG__MAX_CONNECTIONS=[Максимальное количество подключений одновременно]
GOTENBERG__TIMEOUT=[Максимальное время ожидания ответа от сервиса]
GOTENBERG__ANIMATION_TIMEOUT=[Максимальное время ожидания ответа от сервиса]
```
Для скриншотов приложение использует Demo API Gotenberg.

### Запустите MinIO

В отдельном окне PowerShell, запущенном из директории minio, запустите сервис, подставив свой путь до директории. 
Замените пример логина и пароля своими значениями.

```powershell
.\minio.exe server "PATH_TO_FOLDER" --license "[PATH_TO_LICENSE_FILE]"
```
Веб-консоль доступна по адресу `http://127.0.0.1:9001`.
Создайте bucket и укажите его имя в файле .env


### Подключите фронтенд и запустите сервер

Скачайте [готовую сборку фронтенда](https://dvmn.org/filer/canonical/1750917110/1035/) и распакуйте её содержимое в `static/`, чтобы `index.html` оказался в `static/index.html`. Создайте `static/frontend-settings.json`:

```json
{
  "backendBaseUrl": "/frontend-api"
}
```

```powershell
uv run fastapi dev src/main.py
```

- Фронтенд - `http://127.0.0.1:8000/`
- Swagger - `http://127.0.0.1:8000/docs`
- Схема OpenAPI - `http://127.0.0.1:8000/openapi.json`
- Схема локальной установки - [docs/backend_local.png](docs/backend_local.png)
- Схема компонентов бэкенда - [docs/backend_decomposition.png](docs/backend_decomposition.png)

## Как вести разработку

### Проверка и форматирование

```powershell
uv run ruff check src/
uv run ec src/
uv run ruff check --fix src/
uv run ruff format src/
```

`ruff check` проверяет код, `ec` проверяет правила `.editorconfig`. `ruff check --fix`
исправляет доступные нарушения линтера, а `ruff format` форматирует код.

Для справки по локальному `Makefile` выполните `make list`. 
В активированном окружении `make lint` запускает Ruff, а `make format` применяет исправления `ruff check --fix`.


### Хуки

В активированном окружении один раз установите хуки:

```powershell
pre-commit install
```
Перед коммитом хуки проверяют размер добавленных файлов, правила EditorConfig и код через Ruff.

