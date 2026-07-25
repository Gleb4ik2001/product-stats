# Product Stats API

Мини-сервис на Django для автоматического импорта, обработки и выдачи товарной статистики с использованием Pandas, Celery, Redis и PostgreSQL.

---

##  Стек

* **Язык:** Python 3.13
* **Фреймворк:** Django, Django REST Framework
* **Анализ данных:** Pandas
* **База данных:** PostgreSQL
* **Фоновые задачи и планировщик:** Celery, Celery Beat, Redis
* **Кэширование:** Redis
* **Тестирование:** Pytest
* **Линтер:** Ruff
* **Контейнеризация:** Docker, Docker Compose

---

## Быстрый запуск

Сервис полностью готов к запуску одной командой. Вся инфраструктура настроена в `docker-compose.yml` с автоматическим контролем порядка старта (миграции и импорт выполняются до запуска веб-сервера и фоновых задач).

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/Gleb4ik2001/product-stats.git
   cd product-stats
    ```

2. **Создайте файл окружения:**
    Скопируйте пример настроек из `.env.example` в `.env` :
    ```python
        # Django Settings
        SECRET_KEY=django-insecure-qp^ilj8=%v+f8!mjij$2lujm2blyz2emw2il!el!7yqk@1a5u(
        DEBUG=True
        ALLOWED_HOSTS=127.0.0.1,localhost,web,0.0.0.0

        # PostgreSQL Settings
        POSTGRES_DB=stats_db
        POSTGRES_USER=postgres
        POSTGRES_PASSWORD=postgres
        POSTGRES_HOST=db
        POSTGRES_PORT=5432

        # Redis & Celery Settings
        REDIS_URL=redis://redis:6379/0
    ```

3. **Запустите контейнеры:**
    ```bash
    docker compose up --build
    ```

После выполнения команды автоматически:

Запустится и проверит готовность СУБД `PostgreSQL` и `redis`.

Выполнится сервис `migrate`: накатит миграции и совершит первичный импорт тестовых данных.

Запустятся сервисы `web` (API), `celery_worker` и `celery_beat` (периодический импорт).

API будет доступно по адресу: [http://localhost:8000](http://localhost:8000)

## Импорт данных
Импорт данных спроектирован идемпотентным: повторный запуск с теми же данными обновляет существующие записи (по ключу/уникальным полям) и добавляет новые, не создавая дубликатов.

## Варианты запуска импорта:
1. **Ручной запуск через management-команду:**
    ```bash
    docker compose exec web python manage.py import_products
    ```
2. **Запуск через Celery Task:**
    Фоновая задача run_product_import запускается автоматически каждые $N$ минут с помощью Celery Beat (периодичность настраивается в `settings.py`).
3. **Локальный файл с примером данных:**
    На случай недоступности внешнего источника в репозитории предусмотрен резервный файл с тестовыми данными: `sample_products.json`

## Примеры запросов к API (cURL)

1. **Получение списка товаров (с фильтрацией и пагинацией)**
    ```bash
    curl -X GET "http://localhost:8000/api/items/?category=Electronics&price_min=100&price_max=1500&page=1"
    ```
    Пример ответа:
    ```json
    {
    "count": 42,
    "next": "http://localhost:8000/api/items/?page=2",
    "previous": null,
    "results": [
            {
            "id": 1,
            "name": "Wireless Mouse",
            "category": "Electronics",
            "price": "149.99",
            "updated_at": "2026-07-25T10:00:00Z"
            }
        ]
    }
    ```

2. **Средняя цена по категориям (с кэшированием)**
    Агрегированные данные рассчитываются и сохраняются в кэше Redis для обеспечения высокой скорости ответа при повторных запросах.
    ```bash
    curl -X GET "http://localhost:8000/api/stats/avg-price-by-category/"
    ```
    Пример ответа:
    ```json
    [
        {
            "category": "Electronics",
            "avg_price": 284.50
        },
        {
            "category": "Books",
            "avg_price": 18.25
        }
    ]
    ```

## Краткое описание принятых решений
1. **Обработка данных через Pandas:**
    При импорте внешних данных (JSON) используется Pandas для быстрой нормализации: приведения названий колонок к единому стандарту (`external_id`, `name`, `category`, `price`, `updated_at`), очистки от некорректных значений (NaN/null), приведения типов и расчета агрегатов.
2. **Надежность инфраструктуры (Docker Compose):**
    Чтобы избежать состояния гонки (race condition), когда celery_beat пытается прочитать таблицы БД до применения миграций, процесс применения миграций и первоначального импорта вынесен в отдельный сервис `migrate` с политикой `service_completed_successfully`.
3. **Идемпотентность и производительность:**
    Запись данных в PostgreSQL из датафрейма Pandas выполняется пачками `(bulk upsert)`, что гарантирует защиту от дубликатов при регулярном фоновом запуске через Celery Beat.
4. **Кэширование агрегатов:**
    Результат подсчета средней цены кэшируется в `Redis`. При успешном выполнении таски импорта кэш автоматически сбрасывается для поддержания актуальности данных.


## Запуск автотестов
В проекте реализованы модульные и интеграционные тесты `pytest`, проверяющие:
1. Парсинг и нормализацию входных данных через Pandas.
2. Корректность расчета средней цены по категориям.
3. Работу фильтрации и пагинации в эндпоинте `/items`.

Для запуска тестов внутри контейнера выполните:
```bash
docker compose exec web pytest
```
### Спасибо за внимание!

**[Telegram](t.me/daybreak09)**

**[WhatsApp](https://wa.me/+77789405226)**