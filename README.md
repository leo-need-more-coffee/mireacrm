# Mirea CRM

Микросервисная CRM для малого бизнеса сферы услуг: восемь сервисов на Python и Go
за единым API-шлюзом, синхронное взаимодействие по gRPC, асинхронное — через
RabbitMQ и NATS.

**Предметная область.** Сеть ведёт филиалы и специалистов, клиенты записываются на
услуги, на каждую процедуру списываются расходные материалы, за визит выставляется
счёт. Модель нейтральна к нише: барбершоп, студия, автосервис, частная клиника —
везде, где клиент записывается к специалисту на услугу известной длительности,
а на неё расходуются материалы.

```bash
docker compose up -d
curl -s localhost:8000/routes | jq
```

---

## Архитектура

```mermaid
flowchart TB
    UI[Клиент / админка] -->|REST + JWT| GW[API Gateway]
    KC[(Keycloak)] -.->|OIDC| GW

    GW -->|REST| CORE[core-service]
    GW -->|REST| CLI[client-service]
    GW -->|REST| BOOK[booking-service]
    GW -->|REST| CAT[catalog-service]
    GW -->|REST| INV[inventory-service]
    GW -->|REST| BILL[billing-service]
    GW -->|REST| NOTIF[notification-service]
    GW -->|REST| ANA[analytics-service]

    BOOK -->|gRPC| CORE
    BOOK -->|gRPC| CAT
    INV -->|gRPC| CAT
    BILL -->|gRPC| BOOK
    BILL -->|gRPC| CLI
    CLI -->|gRPC| BOOK
    NOTIF -->|gRPC| CLI
    ANA -->|gRPC| CORE

    BOOK -->|events| MQ{{RabbitMQ}}
    CORE --> MQ
    CLI --> MQ
    INV --> MQ
    BILL --> MQ
    MQ --> INV
    MQ --> BILL
    MQ --> NOTIF
    MQ --> ANA

    BOOK -->|slots| NATS{{NATS}}
    INV -->|alerts| NATS
    NATS --> NOTIF
```

`core-service` — центр системы: единственный источник правды об организации
(компании, филиалы, сотрудники, графики). К нему синхронно ходят почти все остальные.

Маршрутизацией он при этом **не** занимается — это дело тонкого `gateway`. Если
свалить обе роли в один сервис, получается распределённый монолит: релиз ядра
кладёт всю систему, а каждый запрос проходит через ядро дважды.

Подробное описание архитектуры со схемами — [`docs/architecture.pdf`](docs/architecture.pdf).

---

## Сервисы

| Сервис | Язык | БД | Роль |
|---|---|---|---|
| [`gateway`](services/gateway/) | Python | — | Проверка JWT, роли, маршрутизация. Единственный публичный порт |
| [`core-service`](services/core-service/) | Python | `core_db` | Компании, филиалы, сотрудники, должности, графики |
| [`client-service`](services/client-service/) | Python | `client_db` | Клиентская база, контакты, лояльность |
| [`booking-service`](services/booking-service/) | Go | `booking_db` | Записи, расписание специалистов, слоты |
| [`catalog-service`](services/catalog-service/) | Python | `catalog_db` | Услуги, прайс, нормативы расхода материалов |
| [`inventory-service`](services/inventory-service/) | Go | `inventory_db` | Склад расходников, списание, остатки |
| [`billing-service`](services/billing-service/) | Python | `billing_db` | Счета, оплаты, комиссия специалиста |
| [`notification-service`](services/notification-service/) | Go | — | Напоминания клиентам, оповещения администраторам |
| [`analytics-service`](services/analytics-service/) | Python | `analytics_db` | Выручка, загрузка специалистов, расход материалов |

У каждого сервиса свой README с описанием ответственности, API и принятых решений.

Go взят там, где он уместен по существу: конкурентная выдача и захват слотов,
счётчики остатков, лёгкий рассыльщик, держащий соединения с двумя брокерами.
Python — там, где ценнее скорость разработки и богатая работа с данными.

---

## Транспорт

Четыре канала, у каждого своя зона ответственности.

### REST — наружу

Всё, что приходит от человека, идёт через `gateway` по HTTP/JSON. Наружу открыт
один порт; сервисы за ним публикуются только на петлю и только для отладки.

### gRPC — между сервисами

Внутренние синхронные вызовы. Контракты в [`proto/`](proto/) — единственный
источник правды, из них генерируются и Python-, и Go-структуры. Это же решает
главную боль разноязычного проекта: рассинхрон контрактов ломает сборку, а не
всплывает на интеграции.

| Вызов | Метод | Зачем |
|---|---|---|
| `booking → core` | `GetEmployeeSchedule`, `GetBranch` | график специалиста, принадлежность филиалу |
| `booking → catalog` | `GetService` | длительность и цена услуги |
| `inventory → catalog` | `GetConsumptionNorms` | норматив расхода материалов на процедуру |
| `billing → booking` | `GetAppointment` | детали визита по `appointment_id` |
| `billing → client` | `AddLoyaltyPoints` | начислить баллы после оплаты |
| `client → booking` | `ListClientAppointments` | история записей для карточки клиента |
| `notification → client` | `GetClientContacts` | контакты и предпочитаемый канал связи |
| `analytics → core` | `GetBranch`, `ListEmployees` | справочник для отчётов |

gRPC-серверы поднимают `core`, `catalog`, `booking` и `client`. Включена рефлексия,
поэтому `grpcurl` работает без `.proto` под рукой.

### RabbitMQ — доменные события

Всё, что меняет состояние системы и что нельзя потерять. Topic-обменник
`mirea.events`, durable-очереди, ручные подтверждения, dead-letter.

| Routing key | Публикует | Потребляют |
|---|---|---|
| `branch.opened` | core | analytics |
| `employee.hired` | core | analytics |
| `client.registered` | client | analytics |
| `appointment.created` | booking | notification, analytics |
| `appointment.cancelled` | booking | notification, analytics |
| `appointment.completed` | booking | inventory, billing, analytics |
| `consumables.written_off` | inventory | analytics |
| `stock.low` | inventory | notification, analytics |
| `invoice.issued` | billing | notification |
| `invoice.paid` | billing | analytics |

`analytics` биндится на `#`, `notification` — на `*.{created,cancelled,low,issued}`.

События намеренно тонкие: несут идентификаторы, а не снимки. Детали потребитель
запрашивает по gRPC, поэтому payload не разрастается и не требует версионирования
при каждом изменении карточки.

### NATS — эфемерный real-time

Широковещательные обновления, где потеря сообщения безвредна, а важны латентность
и отсутствие очередей. Core pub/sub, без JetStream.

| Subject | Публикует | Что это |
|---|---|---|
| `mirea.branch.{id}.schedule` | booking | слот занят или освободился — живое табло на ресепшене |
| `mirea.branch.{id}.alerts` | inventory | «краска заканчивается» администратору филиала прямо сейчас |
| `mirea.heartbeat` | все | presence-сигналы сервисов |

**Почему два брокера.** RabbitMQ несёт доменные события, меняющие состояние:
списание материалов или выставленный счёт потерять нельзя, нужны durable-очереди
и подтверждения. NATS — broadcast без гарантий, где сообщение устаревает за
секунды, а подписчик ресинхронизируется сам. Это разные классы доставки, и
смешивать их в одной шине означает либо переплачивать за надёжность там, где она
не нужна, либо терять её там, где нужна.

Оговорка по существу: проекту такого масштаба хватило бы одного брокера. Второй
взят, чтобы развести оба класса задач явно. NATS-слой изолирован и снимается без
правок доменной логики.

---

## Наблюдаемость

Трассировка и метрики, обе технологии подняты вместе с системой.

### Распределённая трассировка

OpenTelemetry в девяти сервисах, экспорт по OTLP в Jaeger. Один запрос виден
целиком — включая то, что происходит уже после ответа клиенту:

```
POST /appointments/{id}/complete        gateway
  └─ POST /appointments/{id}/complete   booking      захват и закрытие визита
      └─ publish appointment.completed  booking      событие ушло в шину
          ├─ consume appointment.completed  inventory   → GetConsumptionNorms → catalog
          ├─ consume appointment.completed  billing     → GetAppointment → booking
          └─ consume appointment.completed  analytics   → витрины
```

Трасса не рвётся ни на границе языков, ни на границе брокера: контекст едет
в поле `traceparent` конверта события, а потребитель продолжает трассу издателя.
Для этого не понадобилось ничего изобретать — заголовок W3C ходил по системе
с самого начала, оставалось связать его с активным спаном.

Адрес коллектора задаётся переменной `<СЕРВИС>_OTLP_ENDPOINT`; пустое значение
выключает экспорт, поэтому тесты и локальный запуск не требуют инфраструктуры.

### Метрики

Каждый сервис отдаёт `/metrics`, Prometheus собирает их раз в 10 секунд.

| Метрика | О чём |
|---|---|
| `http_requests_total` | запросы по сервису, маршруту и коду ответа |
| `http_request_duration_seconds` | гистограмма времени ответа |
| `grpc_server_requests_total` | вызовы gRPC по методу и коду |
| `domain_events_published_total` | публикация событий по ключу |
| `domain_events_consumed_total` | обработка событий: `handled`, `skipped`, `failed`, `unparsable` |

Метка маршрута — шаблон (`/branches/{branch_id}/employees`), а не фактический
путь: иначе каждый идентификатор в URL заводил бы свой временной ряд.

Отдельно считаются два вида отказов потребителя. `failed` — обработчик вернул
ошибку, `unparsable` — конверт не разобрался вовсе. Второй случай особенно
неприятен тем, что событие уходит в dead-letter молча, и без счётчика заметить
его нечем.

Метрики базы снимает `postgres_exporter`: соединения, транзакции, размеры по
каждой из семи баз.

### Дашборд

Grafana заводит источники данных и панели из [`deploy/grafana`](deploy/grafana/) —
руками настраивать нечего. Дашборд «Mirea CRM — сервисы и база»: нагрузка,
доля ошибок, задержка по 95-му процентилю, самые медленные маршруты, поток
событий, отказы потребителей, вызовы gRPC и состояние базы.

---

## Данные

База на сервис: `core_db`, `client_db`, `booking_db`, `catalog_db`, `inventory_db`,
`billing_db`, `analytics_db`. Сервисы не ходят в чужие базы — только через API.

Физически это **один инстанс Postgres** с семью базами и отдельным пользователем на
каждую. Восемь контейнеров Postgres ноутбук переживёт плохо, а изоляция схемы при
этом соблюдена: в чужую базу сервис не попадёт даже случайно.

`notification-service` без базы: шаблоны в конфигурации, история отправок в логах.

Инварианты, которые нельзя доверить приложению, живут в базе: непересекающиеся
смены и захват слота — ограничения `EXCLUDE USING gist`, неотрицательный остаток —
`CHECK`. Под гонкой это единственная надёжная защита.

---

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d
```

Поднимется инфраструктура и все девять контейнеров. Единственный вход — шлюз на
`:8000`. Токен выдаёт Keycloak; на отладке удобнее через шлюз:

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"owner","password":"owner"}' | jq -r .access_token)

curl -s localhost:8000/routes | jq                 # какие запросы есть и кому доступны
curl -s localhost:8000/templates -H "Authorization: Bearer $TOKEN"
```

Учётные записи создаются при импорте realm:

| Учётная запись | Пароль | Роль |
|---|---|---|
| `owner` | `owner` | `admin` |
| `admin-tverskaya` | `manager` | `manager` |
| `specialist-anna` | `specialist` | `specialist` |

Пароли одноразовые и предназначены только для локального запуска.

| Что | Адрес | Доступ |
|---|---|---|
| Шлюз — вход в систему | http://localhost:8000 | токен Keycloak |
| Keycloak | http://localhost:8080 | `admin` / `admin` |
| RabbitMQ, панель | http://localhost:15672 | `guest` / `guest` |
| NATS, мониторинг | http://localhost:8222 | — |
| Postgres | `localhost:5432` | свой пользователь на каждую базу |
| Jaeger — трассировка | http://localhost:16686 | — |
| Grafana — дашборды | http://localhost:3000 | `admin` / `admin`, чтение без входа |
| Prometheus | http://localhost:9090 | — |

Обменник `mirea.events`, очереди потребителей и dead-letter объявляются
декларативно из [`deploy/rabbitmq/definitions.json`](deploy/rabbitmq/definitions.json):
после `docker compose down -v` топология восстанавливается сама.

---

## Разработка

Сгенерированный из контрактов код хранится в репозитории, поэтому для сборки
`buf` не нужен. Он нужен только при изменении `.proto`:

```bash
go install github.com/bufbuild/buf/cmd/buf@latest
buf lint
buf generate          # обновит gen/go и gen/python
```

Тесты — 212, два вида: unit без ввода-вывода и интеграционные против настоящего
Postgres. Интеграционным нужен запущенный `docker compose up -d postgres`.

```bash
# Python-сервис
cd services/core-service
python -m venv .venv && .venv/bin/pip install -e ".[dev]" -e ../../gen/python
.venv/bin/python -m pytest
.venv/bin/ruff check .

# Go-сервис
cd services/booking-service
go test ./...                      # unit
go test -tags integration ./...    # плюс интеграционные
```

Интеграционные тесты на Go отделены признаком сборки `integration`, на Python — по
каталогам `tests/unit` и `tests/integration`.

---

## Структура репозитория

```
.
├── proto/              контракты Protocol Buffers — единственный источник правды
├── gen/                сгенерированный код: gen/go и gen/python
├── buf.yaml            модуль и правила линтинга контрактов
├── buf.gen.yaml        настройки генерации
├── services/           восемь сервисов и шлюз, у каждого свой README
├── deploy/             init-скрипты Postgres, топология RabbitMQ, realm Keycloak
├── docs/               описание архитектуры, глоссарий, исходники отчёта
└── docker-compose.yml  инфраструктура и сервисы
```

---

## Документация

| Документ | О чём |
|---|---|
| [`docs/architecture.pdf`](docs/architecture.pdf) | Описание системы на 19 страниц: декомпозиция, транспорт, события, данные, сквозные решения и разбор каждого сервиса. Пять векторных схем |
| [`docs/glossary.md`](docs/glossary.md) | Единый язык: сущности, события, команды, действующие лица, бизнес-правила |
| `docs/report-*.py` | Исходники сборки отчёта — формулировку или схему можно поправить и пересобрать |

---

## Состояние

| Сервис | Готовность |
|---|---|
| `core-service` | REST, gRPC, события, Docker, 40 тестов |
| `booking-service` | REST, gRPC, RabbitMQ, NATS, Docker, 34 теста |
| `catalog-service` | REST, gRPC, Docker, 13 тестов |
| `inventory-service` | REST, потребитель событий, RabbitMQ, NATS, Docker, 20 тестов |
| `client-service` | REST, gRPC в обе стороны, Docker, 14 тестов |
| `billing-service` | REST, потребитель событий, gRPC-клиент, Docker, 15 тестов |
| `notification-service` | REST, потребитель RabbitMQ и NATS, Docker, 10 тестов |
| `analytics-service` | REST, потребитель `#`, gRPC-клиент, Docker, 16 тестов |
| `gateway` | OIDC, роли, проброс личности, Docker, 50 тестов |

Система работает целиком: запись проходит через три сервиса синхронно, завершение
визита расходится на трёх потребителей асинхронно, аналитика видит весь поток.

**В планах:** конвейеры непрерывной интеграции.

---

## Учебный контекст

Проект выполнен в рамках курса «Микросервисная архитектура» (МИРЭА). Соответствие
разделов репозитория практическим работам:

| Работа | Тема | Где |
|---|---|---|
| 1–2 | Доменные события, команды, действующие лица, бизнес-правила | [`docs/glossary.md`](docs/glossary.md) |
| 3–4 | Агрегаты, ограниченные контексты, связи и стили общения | [`docs/architecture.pdf`](docs/architecture.pdf), разделы 2–6 |
| 6 | Сервисы, вложенные вызовы, Docker Compose | [`services/`](services/), `docker-compose.yml` |
| 8 | Два вида тестирования | `tests/` в каждом сервисе |
| 9 | Keycloak, OIDC, проверка токена на шлюзе | [`services/gateway/`](services/gateway/) |
| 10 | Трассировка и метрики | раздел «Наблюдаемость», [`deploy/grafana`](deploy/grafana/) |
