# Курси валют до UAH

Django 5 + DRF + Celery + Redis + PostgreSQL. Курси з [Monobank `/bank/currency`](https://api.monobank.ua/bank/currency). **Нові** запити з Monobank пишуться лише для валют зі списку відстеження з **`is_active=True`**. Уже збережена **історія не видаляється**, якщо валюту прибрали з треку — лише перестають додаватися нові точки. Оновлення кожні **5 хв** (**django-celery-beat**, задача `fetch-monobank-uah-rates` — міграція `0002`).

**Адмінка (superuser):** **Django Celery Results** → Task results, **Django Celery Beat** → Periodic tasks.


OpenAPI: `/api/schema/`, Swagger: `/api/docs/swagger/`, ReDoc: `/api/docs/redoc/`.

## API

| Метод | Шлях |
|--------|------|
| GET | `/api/tracked-currencies/` — відстежувані + поточний курс |
| POST | `/api/tracked-currencies/` — `{"iso_numeric_code": 840}` |
| PATCH | `/api/tracked-currencies/{id}/` — `{"is_active": false}` |
| GET | `/api/currencies/available/` — з Monobank, ще не в списку |
| GET | `/api/rates/history/?currency=840&date_from=&date_to=` — лише для відстежуваних |

## CSV

Усе зводиться до однієї функції `tracked_currencies_to_dataframe()` у `currencies/export_rates.py` (pandas: список словників → `DataFrame` → `to_csv`).

- **Адмінка** → відстежувані валюти → дія **«Завантажити CSV…»**.
- **Команда:** `python manage.py export_rates_csv -o rates.csv` (є `--only-active`).

## Локально

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
```

Три процеси: `runserver`, `celery -A config worker -l info`, `celery -A config beat -l info`.

**Windows:** якщо бачиш `PermissionError: WinError 5` / `semlock` у воркері — у `config/celery.py` для Windows уже виставлено пул **`solo`** (без дочірніх процесів). У Docker/Linux лишається звичайний **prefork**.

Разове оновлення (корисно одразу після додавання валюти, поки Beat ще не встиг):  
`python manage.py shell -c "from currencies.services import store_uah_rates_from_monobank; print(store_uah_rates_from_monobank())"`

Monobank часто відповідає **429**, якщо запитувати API занадто часто.

## Docker

```bash
docker compose up --build
```

Коди валют — **ISO 4217 numeric**; три літери (USD тощо) дістаємо функцією `get_currency_alpha()` у `utils.py` через `pycountry`.

TODO : Треба прибрати змiну datetime у store_uah_rates_from_monobank, створена тільки щоб перевірити логіку зберігання без очікування оновлення рейтів в МОНО.
