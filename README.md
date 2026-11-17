# Мониторинг образования Хабаровского края (Streamlit)

Готовый русскоязычный интерфейс для **PostgreSQL** и демонстрационной схемы `edu_khv`.
Данные полностью вымышленные, **не являются официальной статистикой**.

## Возможности

- Главная страница: количество школ, педагогов, учащихся и территорий, диаграммы, сводка.
- Просмотр **всех 18 таблиц и 3 представлений** исходного SQL с русскими названиями таблиц **и столбцов**.
- Поиск по значениям полей, фильтры по территории, школе и учебному году там, где эти измерения применимы.
- Постраничный просмотр, выгрузка CSV с русскими заголовками (UTF-8 BOM для Excel).
- Текстовые названия связанных справочников рядом с внешними ключами.
- Отдельная статистика по ЕГЭ и ОГЭ: без смешивания шкал оценок.
- Только SQL `SELECT`; изменение записей из интерфейса не предусмотрено.

## Локальный запуск

1. Создайте **пустую** базу PostgreSQL, например `khv_demo`.
2. Запустите файл `sql/khabarovsk_education_demo.sql` в этой базе через pgAdmin или psql:

   ```bash
   psql -h localhost -U postgres -d khv_demo -f sql/khabarovsk_education_demo.sql
   ```

   **Внимание:** этот SQL при повторном запуске **удаляет и пересоздаёт схему `edu_khv`**.

3. Установите зависимости:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Создайте `.streamlit/secrets.toml` по образцу `.streamlit/secrets.toml.example`, укажите свои реквизиты доступа.

5. Запустите приложение:

   ```bash
   python -m streamlit run app.py
   ```

   Стандартный адрес после запуска: `http://localhost:8501`. В Windows можно затем запускать `start_windows.bat`.

## Публикация в Streamlit Community Cloud

1. Разместите папку проекта в своём репозитории GitHub; **не публикуйте `.streamlit/secrets.toml`**.
2. В Streamlit Community Cloud создайте приложение из репозитория, главный файл — `app.py`.
3. В настройках приложения добавьте **Secrets**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, при необходимости `DB_SSLMODE = "require"`; либо одну строку `DATABASE_URL`.
4. PostgreSQL должен быть **доступен с облачного сервера Streamlit**. База на `localhost` домашнего компьютера из облака недоступна. Для публичного приложения рекомендуется отдельный **read-only** пользователь PostgreSQL, сетевые ограничения и SSL.
5. Проверьте запуск приложения. Для эксплуатации в интернете обязательно включите ограничения доступа, если данные не предназначены всем.

### Пользователь PostgreSQL с правами только на чтение (необязательно)

Под администратором БД:

```sql
CREATE ROLE edu_viewer LOGIN PASSWORD 'замените_на_сложный_пароль';
GRANT CONNECT ON DATABASE khv_demo TO edu_viewer;
GRANT USAGE ON SCHEMA edu_khv TO edu_viewer;
GRANT SELECT ON ALL TABLES IN SCHEMA edu_khv TO edu_viewer;
ALTER DEFAULT PRIVILEGES IN SCHEMA edu_khv GRANT SELECT ON TABLES TO edu_viewer;
```

Если ваше имя базы отличается от `khv_demo`, замените его в `GRANT CONNECT`.

## Устройство проекта

- `app.py` — код приложения на Streamlit.
- `sql/khabarovsk_education_demo.sql` — структура и генерация тестовых данных.
- `.streamlit/secrets.toml.example` — шаблон настройки подключения.
- `requirements.txt` — зависимости.

Приложение рассчитано на демонстрационную структуру из приложенного SQL. Если вы измените схему, потребуется согласовать с ней названия полей в `app.py`.
"# educ" 
