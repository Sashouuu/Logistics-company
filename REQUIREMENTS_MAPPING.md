# Логистична Компания - Документация на Изискванията

## Обзор

Този документ съпоставя всички изисквания на приложението с точните местоположения на код, който ги имплементира.

---

## ИЗИСКВАНЕ 1: Регистриране на потребители и вход в системата

### Описание
Потребителите трябва да могат да се регистрират с електронна поща и парола, и да се влизане в системата.

### Местоположение на Код

#### Регистриране на потребител
- **Файл:** [backend/routes/auth.py](backend/routes/auth.py#L11-L65)
- **Функция:** `register()` (редове 11-65)
- **Описание:** 
  - POST endpoint `/api/auth/register`
  - Валидира електронна поща, парола и роля
  - Криптира парола с `generate_password_hash()`
  - Създава User запис в БД
  - Създава допълнителен профил (Client или Employee) в зависимост от ролята

#### Вход в системата
- **Файл:** [backend/routes/auth.py](backend/routes/auth.py#L68-L87)
- **Функция:** `login()` (редове 68-87)
- **Описание:**
  - POST endpoint `/api/auth/login`
  - Проверява email и парола с `check_password()`
  - Генерира JWT токен с роля на потребителя
  - Връща токен, user_id и role

#### User Модел
- **Файл:** [backend/models/user.py](backend/models/user.py#L1-L23)
- **Клас:** `User` (редове 1-23)
- **Полета:**
  - `id` - Primary key
  - `email` - Уникален електронен адрес
  - `password_hash` - Криптирана парола
  - `role` - CLIENT или EMPLOYEE
  - `created_at` - Дата на създаване

- **Методи:**
  - `set_password()` (редове 15-17) - Криптиране на парола
  - `check_password()` (редове 19-21) - Проверка на парола при вход

---

## ИЗИСКВАНЕ 2: Възможност за задаване на роли на потребителите (служител, клиент)

### Описание
При регистриране, потребителят получава роля: CLIENT (клиент) или EMPLOYEE (служител). Всяка роля има различни права.

### Местоположение на Код

#### User Модел - Роля
- **Файл:** [backend/models/user.py](backend/models/user.py#L13)
- **Поле:** `role` (ред 13)
- **Стойности:** "CLIENT" или "EMPLOYEE"

#### Регистриране с Роля
- **Файл:** [backend/routes/auth.py](backend/routes/auth.py#L20-L27)
- **Функция:** `register()` (редове 20-27)
- **Описание:**
  - Приема роля при регистриране
  - Валидира че роля е CLIENT или EMPLOYEE
  - Създава съответния профил (Client или Employee)

#### JWT Токен със Роля
- **Файл:** [backend/routes/auth.py](backend/routes/auth.py#L82-L85)
- **Функция:** `login()` (редове 82-85)
- **Описание:**
  - Включва роля в JWT токена като `additional_claims={"role": user.role}`
  - Позволява проверка на роля с `get_jwt()` във всеки endpoint

#### Authorization Check Pattern
Всички endpoints проверяват роля:
```python
claims = get_jwt()
if claims.get("role") != "EMPLOYEE":
    return jsonify({"error": "Unauthorized"}), 403
```

---

## ИЗИСКВАНЕ 3: CRUD операции за основни данни

### 3a. Логистична Компания (Company)

#### Company Модел
- **Файл:** [backend/models/company.py](backend/models/company.py)
- **Полета:**
  - `name` - Име на компанията
  - `registration_number` - Регистрационен номер
  - `address` - Адрес
  - `phone` - Телефон
  - `email` - Email

#### CRUD Операции
- **Файл:** [backend/routes/company.py](backend/routes/company.py)

| Операция | Функция | Редове | HTTP | Path |
|----------|---------|--------|------|------|
| Create | `create_company()` | 33-53 | POST | `/api/company` |
| Read (всички) | `get_companies()` | 10-21 | GET | `/api/company` |
| Read (един) | `get_company()` | 24-31 | GET | `/api/company/<id>` |
| Update | `update_company()` | 56-80 | PUT | `/api/company/<id>` |
| Delete | `delete_company()` | 83-99 | DELETE | `/api/company/<id>` |

**Забележка:** Само служители (EMPLOYEE) могат да използват тези операции

---

### 3b. Служител на компанията (Employee)

#### Employee Модел
- **Файл:** [backend/models/employee.py](backend/models/employee.py)
- **Полета:**
  - `user_id` - Link към User
  - `company_id` - Link към Company
  - `office_id` - Link към Office
  - `first_name`, `last_name` - Име
  - `phone` - Телефон
  - `hire_date` - Дата на наемане
  - `is_active` - Статус

#### CRUD Операции
- **Файл:** [backend/routes/employee.py](backend/routes/employee.py)

| Операция | Функция | Редове | HTTP | Path |
|----------|---------|--------|------|------|
| Create | `create_employee()` | 42-68 | POST | `/api/employee` |
| Read (всички) | `get_employees()` | 11-31 | GET | `/api/employee` |
| Read (един) | `get_employee()` | 34-41 | GET | `/api/employee/<id>` |
| Update | `update_employee()` | 71-101 | PUT | `/api/employee/<id>` |
| Delete | `delete_employee()` | 104-117 | DELETE | `/api/employee/<id>` |

**Забележка:** Само служители (EMPLOYEE) могат да управляват служители

---

### 3c. Клиент на компанията (Client)

#### Client Модел
- **Файл:** [backend/models/client.py](backend/models/client.py)
- **Полета:**
  - `user_id` - Link към User
  - `company_name` - Име на компания
  - `first_name`, `last_name` - Име
  - `phone` - Телефон
  - `address`, `city`, `country` - Адрес
  - `is_active` - Статус

#### CRUD Операции
- **Файл:** [backend/routes/client.py](backend/routes/client.py)

| Операция | Функция | Редове | HTTP | Path |
|----------|---------|--------|------|------|
| Create | `create_client()` | 59-85 | POST | `/api/client` |
| Read (всички) | `get_clients()` | 12-39 | GET | `/api/client` |
| Read (един) | `get_client()` | 68-75 | GET | `/api/client/<id>` |
| Read (свой профил) | `get_current_client()` | 42-65 | GET | `/api/client/me` |
| Update | `update_client()` | 88-126 | PUT | `/api/client/<id>` |
| Delete | `delete_client()` | 129-147 | DELETE | `/api/client/<id>` |

**Забележка:** 
- Служители могат да управляват всички клиенти
- Клиентите могат да обновят само своя профил

---

### 3d. Офис на компанията (Office)

#### Office Модел
- **Файл:** [backend/models/office.py](backend/models/office.py)
- **Полета:**
  - `name` - Име на офис
  - `company_id` - Link към Company
  - `address`, `city`, `country` - Адрес
  - `phone`, `email` - Контакти

#### CRUD Операции
- **Файл:** [backend/routes/office.py](backend/routes/office.py)

| Операция | Функция | Редове | HTTP | Path |
|----------|---------|--------|------|------|
| Create | `create_office()` | 37-61 | POST | `/api/office` |
| Read (всички) | `get_offices()` | 10-28 | GET | `/api/office` |
| Read (един) | `get_office()` | 31-38 | GET | `/api/office/<id>` |
| Update | `update_office()` | 64-90 | PUT | `/api/office/<id>` |
| Delete | `delete_office()` | 93-109 | DELETE | `/api/office/<id>` |

**Забележка:** Само служители (EMPLOYEE) могат да управляват офиси

---

### 3e. Пратка (Shipment)

#### Shipment Модел
- **Файл:** [backend/models/shipment.py](backend/models/shipment.py)
- **Полета:**
  - `sender_id` - Изпращач (Client)
  - `receiver_id` - Получател (Client)
  - `registered_by_employee_id` - Служител, който регистрира пратката
  - `tracking_number` - Номер за проследяване
  - `weight`, `dimensions` - Размери
  - `price` - Цена (за приход)
  - `sent_date`, `received_date` - Дати
  - `status` - PENDING, IN_TRANSIT, DELIVERED, CANCELLED
  - `origin_address`, `destination_address` - Адреси

#### CRUD Операции
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py)

| Операция | Функция | Редове | HTTP | Path |
|----------|---------|--------|------|------|
| Create | `create_shipment()` | 56-122 | POST | `/api/shipment` |
| Read (всички) | `get_shipments()` | 18-45 | GET | `/api/shipment` |
| Read (един) | `get_shipment()` | 48-68 | GET | `/api/shipment/<id>` |
| Update | `update_shipment()` | 125-156 | PUT | `/api/shipment/<id>` |
| Delete | `delete_shipment()` | 159-183 | DELETE | `/api/shipment/<id>` |

**Забележка:** 
- Служители видят всички пратки
- Клиентите видят само своите пратки (изпратени или получени)

---

## ИЗИСКВАНЕ 4: Служителите регистрират изпратени и получени пратки

### Описание
Служителите (EMPLOYEE) могат да регистрират нови пратки в системата и могат да обновят статуса на пратките, включително да маркират дата на получаване.

### Местоположение на Код

#### Регистриране на Пратка
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L56-L122)
- **Функция:** `create_shipment()` (редове 56-122)
- **Описание:**
  - POST endpoint `/api/shipment`
  - Служител предоставя:
    - `sender_id` - Който изпраща
    - `receiver_id` - Който получава
    - `registered_by_employee_id` - Служител, който регистрира
    - Детайли на пратката (трекинг номер, тегло, размери, описание, цена)
  - Клиент може да регистрира само своя пратка (системата автоматично присвоява служител)

#### Обновяване на Статус на Пратка
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L125-L156)
- **Функция:** `update_shipment()` (редове 125-156)
- **Описание:**
  - PUT endpoint `/api/shipment/<id>`
  - Служител може да обновя:
    - `status` - Ново състояние (PENDING, IN_TRANSIT, DELIVERED, CANCELLED)
    - `received_date` - Дата на получаване когато статус е DELIVERED
  - Други детайли на пратката

#### Shipment Модел - Връзки
- **Файл:** [backend/models/shipment.py](backend/models/shipment.py#L22-L25)
- **Отношения:**
  - `sender_id` - Link към Client (който изпраща)
  - `receiver_id` - Link към Client (който получава)
  - `registered_by_employee_id` - Link към Employee (служител, който регистрира)

#### Employee Модел - Регистрирани Пратки
- **Файл:** [backend/models/employee.py](backend/models/employee.py#L24-L26)
- **Отношение:** `shipments_registered` - Всички пратки, регистрирани от служител

---

## ИЗИСКВАНЕ 5: Справки (Reports)

### 5a. Всички служители в компанията

#### Endpoint
- **Файл:** [backend/routes/employee.py](backend/routes/employee.py#L11-L31)
- **Функция:** `get_employees()` (редове 11-31)
- **HTTP:** GET `/api/employee`
- **Филтър:** `?company_id=<id>` (опционално)
- **Кой może:** Само служители (EMPLOYEE)
- **Описание:** Връща всички служители, опционално филтрирани по компания

---

### 5b. Всички клиенти на компанията

#### Endpoint
- **Файл:** [backend/routes/client.py](backend/routes/client.py#L12-L39)
- **Функция:** `get_clients()` (редове 12-39)
- **HTTP:** GET `/api/client`
- **Кой може:** Служители видят всички клиенти, клиентите видят другите (за избор на получател)
- **Описание:** Връща всички клиенти

---

### 5c. Всички пратки, които са били регистрирани

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L191-L202)
- **Функция:** `report_all_shipments()` (редове 191-202)
- **HTTP:** GET `/api/shipment/reports/all-shipments`
- **Кой може:** Само служители (EMPLOYEE)
- **Описание:** Връща всички пратки в системата

---

### 5d. Всички пратки, регистрирани от даден служител

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L205-L216)
- **Функция:** `report_shipments_by_employee()` (редове 205-216)
- **HTTP:** GET `/api/shipment/reports/by-employee/<employee_id>`
- **Кой може:** Само служители (EMPLOYEE)
- **Параметър:** `employee_id` - ID на служител
- **Описание:** Филтрира пратки по служител, който ги регистрира

---

### 5e. Всички пратки, които са изпратени, но не са получени

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L219-L234)
- **Функция:** `report_undelivered_shipments()` (редове 219-234)
- **HTTP:** GET `/api/shipment/reports/undelivered`
- **Кой може:** Само служители (EMPLOYEE)
- **Описание:** 
  - Филтрира пратки със статус != "DELIVERED" И != "CANCELLED"
  - Връща пратки в статус PENDING или IN_TRANSIT

---

### 5f. Всички пратки, изпратени от даден клиент

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L237-L258)
- **Функция:** `report_shipments_by_sender()` (редове 237-258)
- **HTTP:** GET `/api/shipment/reports/by-sender/<client_id>`
- **Кой може:** Служители видят всички, клиенти видят само своите
- **Параметър:** `client_id` - ID на клиент
- **Описание:** Връща всички пратки, изпратени от дадения клиент

---

### 5g. Всички пратки, получени от даден клиент

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L261-L282)
- **Функция:** `report_shipments_by_receiver()` (редове 261-282)
- **HTTP:** GET `/api/shipment/reports/by-receiver/<client_id>`
- **Кой може:** Служители видят всички, клиенти видят само своите
- **Параметър:** `client_id` - ID на клиент
- **Описание:** Връща всички пратки, получени от дадения клиент

---

### 5h. Всички приходи за определен период

#### Endpoint
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L285-L312)
- **Функция:** `report_company_revenue()` (редове 285-312)
- **HTTP:** GET `/api/shipment/reports/revenue`
- **Кой може:** Само служители (EMPLOYEE)
- **Параметри:** 
  - `start_date` - Начална дата (ISO format, опционално)
  - `end_date` - Крайна дата (ISO format, опционално)
- **Описание:**
  - Филтрира пратки по дата на изпращане (sent_date)
  - Сумира цените (price) на всички пратки в периода
  - Връща общия приход и брой пратки

---

## ИЗИСКВАНЕ 6: Служителите видят всички пратки

### Описание
Служителите имат достъп до всички пратки в системата, независимо дали ги регистрирали или не.

### Местоположение на Код

#### Get All Shipments - Employee View
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L18-L45)
- **Функция:** `get_shipments()` (редове 18-45)
- **HTTP:** GET `/api/shipment`
- **Логика (редове 25-27):**
```python
if role == "EMPLOYEE":
    # REQUIREMENT 6: Employees see all shipments
    shipments = Shipment.query.all()
```

---

## ИЗИСКВАНЕ 7: Клиентите видят пратките, които са изпратили или получили

### Описание
Клиентите могат да видят само пратките, в които са участници (като изпращач или получател).

### Местоположение на Код

#### Get All Shipments - Client View
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L29-L40)
- **Функция:** `get_shipments()` (редове 29-40)
- **HTTP:** GET `/api/shipment`
- **Логика (редове 30-40):**
```python
else:  # CLIENT
    # REQUIREMENT 7: Clients see only their own shipments (sent or received)
    client = Client.query.filter_by(user_id=user_id).first()
    shipments = Shipment.query.filter(
        or_(Shipment.sender_id == client.id, Shipment.receiver_id == client.id)
    ).all()
```

#### Get Single Shipment - Authorization Check
- **Файл:** [backend/routes/shipment.py](backend/routes/shipment.py#L48-L68)
- **Функция:** `get_shipment()` (редове 48-68)
- **Логика (редове 64-66):**
```python
if role == "CLIENT":
    # REQUIREMENT 7: Verify client owns the shipment
    if client.id != shipment.sender_id and client.id != shipment.receiver_id:
        return jsonify({"error": "Unauthorized"}), 403
```

#### Client Модел - Отношения
- **Файл:** [backend/models/client.py](backend/models/client.py#L26-L29)
- **Отношения:**
  - `shipments_sent` - Всички пратки, които е изпратил
  - `shipments_received` - Всички пратки, които е получил

---

## Резюме на Изисквания

| № | Изискване | Статус | Основни Файлове |
|---|-----------|--------|------------------|
| 1 | Регистриране и Вход | ✅ | auth.py, user.py |
| 2 | Роли (Client/Employee) | ✅ | user.py, auth.py |
| 3a | Company CRUD | ✅ | company.py, company model |
| 3b | Employee CRUD | ✅ | employee.py, employee model |
| 3c | Client CRUD | ✅ | client.py, client model |
| 3d | Office CRUD | ✅ | office.py, office model |
| 3e | Shipment CRUD | ✅ | shipment.py, shipment model |
| 4 | Служители регистрират пратки | ✅ | shipment.py (create/update) |
| 5a | Справка служители | ✅ | employee.py (get_employees) |
| 5b | Справка клиенти | ✅ | client.py (get_clients) |
| 5c | Справка всички пратки | ✅ | shipment.py (report_all_shipments) |
| 5d | Справка по служител | ✅ | shipment.py (report_by_employee) |
| 5e | Справка недостигнали пратки | ✅ | shipment.py (report_undelivered) |
| 5f | Справка пратки от клиент | ✅ | shipment.py (report_by_sender) |
| 5g | Справка пратки към клиент | ✅ | shipment.py (report_by_receiver) |
| 5h | Справка приход за период | ✅ | shipment.py (report_revenue) |
| 6 | Служители видят всички | ✅ | shipment.py (get_shipments) |
| 7 | Клиенти видят свои пратки | ✅ | shipment.py (get_shipments) |

---

## Архитектура на Безопасност

### JWT Authentication
- Всеки endpoint изисква `@jwt_required()` decorator
- Роля се включва в токена като `additional_claims={"role": user.role}`
- Всяка операция проверява роля с `claims.get("role")`

### Authorization Pattern
```python
@endpoint.method("")
@jwt_required()
def handler():
    claims = get_jwt()
    if claims.get("role") != "REQUIRED_ROLE":
        return jsonify({"error": "Unauthorized"}), 403
```

### Данни според Роля
- **EMPLOYEE:** Достъп до управление на служители, клиенти, компании, офиси, пратки, справки
- **CLIENT:** Достъп до своя профил, регистриране на собствени пратки, видяване на свои пратки

---

## База на Данни - Entity Relationships

```
User (1) ──→ (1) Employee  (регистриран служител)
User (1) ──→ (1) Client    (регистриран клиент)

Employee (1) ──→ (M) Shipment  (registered_by_employee_id)
Company (1) ──→ (M) Employee
Company (1) ──→ (M) Office
Office (1) ──→ (M) Employee

Client (1) ──→ (M) Shipment    (sender_id)
Client (1) ──→ (M) Shipment    (receiver_id)
Employee (1) ──→ (M) Shipment  (registered_by_employee_id)
```

---

## Тестване на Функционалност

### Тест на Регистриране
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "client@example.com",
  "password": "secure123",
  "role": "CLIENT",
  "company_name": "ABC Company",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+359123456789",
  "address": "123 Main St",
  "city": "Sofia",
  "country": "Bulgaria"
}
```

### Тест на Вход
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "client@example.com",
  "password": "secure123"
}
```

### Тест на CRUD Операция с JWT
```bash
GET /api/shipment
Authorization: Bearer <JWT_TOKEN>
```

---

## Константи и Статусни Кодове

### Статусни Кодове на Пратка
- `PENDING` - Чакаща обработка
- `IN_TRANSIT` - В пътя
- `DELIVERED` - Доставена
- `CANCELLED` - Отменена

### HTTP Response Codes
- `200` - OK (успешна операция)
- `201` - Created (успешно създаване)
- `400` - Bad Request (грешни параметри)
- `403` - Forbidden (недостатъчни права)
- `404` - Not Found (ресурс не намерен)

---

**Последна актуализация:** January 28, 2026
**Версия:** 1.0
