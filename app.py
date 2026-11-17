"""Демонстрационный интерфейс мониторинга образования Хабаровского края.
Источник: PostgreSQL, схема edu_khv (данные полностью синтетические).
"""

from __future__ import annotations

import math
import os
from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

st.set_page_config(
    page_title="Образование Хабаровского края",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Все 18 таблиц исходного SQL и три представления.
# Приведённые ниже имена — только контролируемые константы приложения.
TABLES: dict[str, dict[str, Any]] = {
    "schools": {"title": "Школы", "group": "Школы и обучение", "fields": {
        "id": "ID школы", "municipality_id": "ID территории", "name": "Наименование школы",
        "address": "Адрес", "students_count": "Количество учащихся",
        "location": "Населённый пункт", "teachers_count": "Количество педагогов"}},
    "school_infrastructure": {"title": "Инфраструктура школ", "group": "Школы и обучение", "fields": {
        "id": "ID записи", "school_id": "ID школы", "classrooms_count": "Количество кабинетов",
        "school_buses_count": "Количество школьных автобусов", "has_library": "Есть библиотека",
        "has_life_safety_classroom": "Есть кабинет ОБЖ", "has_computer_class": "Есть компьютерный класс",
        "has_gym": "Есть спортивный зал", "has_canteen": "Есть столовая",
        "has_sports_ground": "Есть спортивная площадка", "has_accessible_environment": "Есть доступная среда",
        "has_medical_room": "Есть медицинский кабинет", "has_swimming_pool": "Есть бассейн",
        "has_growth_center": "Есть центр «Точка роста»", "medical_staff_count": "Количество медработников",
        "has_wifi": "Есть Wi-Fi", "computers_count": "Количество компьютеров"}},
    "teachers": {"title": "Педагоги", "group": "Школы и обучение", "fields": {
        "id": "ID педагога", "school_id": "ID школы", "average_experience_years": "Стаж работы, лет",
        "qualification_level_id": "ID квалификационной категории",
        "weekly_load_hours": "Нагрузка, часов в неделю", "subject_id": "ID предмета",
        "has_additional_training": "Прошёл повышение квалификации",
        "education_level_id": "ID уровня образования"}},
    "classes": {"title": "Классы", "group": "Школы и обучение", "fields": {
        "id": "ID класса", "school_id": "ID школы", "academic_year_id": "ID учебного года",
        "class_profile_id": "ID профиля класса", "grade_number": "Номер класса",
        "class_letter": "Буква класса", "is_graduating": "Выпускной класс",
        "students_count": "Количество учащихся"}},
    "class_student_stats": {"title": "Статистика учащихся классов", "group": "Школы и обучение", "fields": {
        "id": "ID записи", "class_id": "ID класса", "immigrant_students_count": "Количество учащихся-мигрантов",
        "repeaters_count": "Количество оставшихся на второй год"}},
    "graduates": {"title": "Выпускники", "group": "Результаты и достижения", "fields": {
        "id": "ID выпуска", "class_id": "ID класса", "graduates_count": "Количество выпускников",
        "honors_count": "Количество отличников", "medalists_count": "Количество медалистов",
        "certificates_received": "Получили аттестат", "certificates_not_received": "Не получили аттестат"}},
    "graduate_admissions": {"title": "Поступление выпускников", "group": "Результаты и достижения", "fields": {
        "id": "ID записи", "graduate_id": "ID выпуска", "admission_profile_id": "ID направления поступления",
        "admitted_count": "Количество поступивших", "khabarovsk_krai_percent": "Доля поступивших в Хабаровском крае, %"}},
    "exam_results": {"title": "Результаты экзаменов", "group": "Результаты и достижения", "fields": {
        "id": "ID результата", "class_id": "ID класса", "exam_type_id": "ID типа экзамена",
        "subject_id": "ID предмета", "average_score": "Средний балл",
        "participants_count": "Количество сдававших", "passed_percent": "Доля сдавших, %"}},
    "school_ratings": {"title": "Рейтинг школ", "group": "Результаты и достижения", "fields": {
        "id": "ID записи", "school_id": "ID школы", "academic_year_id": "ID учебного года",
        "ranking_place": "Место в рейтинге"}},
    "olympiads": {"title": "Олимпиады", "group": "Результаты и достижения", "fields": {
        "id": "ID результата", "name": "Название олимпиады", "subject_id": "ID предмета",
        "school_id": "ID школы", "academic_year_id": "ID учебного года",
        "result": "Результат"}},
    "municipalities": {"title": "Муниципальные образования", "group": "Справочники", "fields": {
        "id": "ID территории", "name": "Название территории",
        "administrative_center": "Административный центр", "population": "Население (демо)",
        "school_age_population": "Население школьного возраста (демо)"}},
    "academic_years": {"title": "Учебные годы", "group": "Справочники", "fields": {
        "id": "ID учебного года", "name": "Учебный год", "start_date": "Дата начала",
        "end_date": "Дата окончания"}},
    "subjects": {"title": "Учебные предметы", "group": "Справочники", "fields": {
        "id": "ID предмета", "name": "Название предмета"}},
    "exam_types": {"title": "Типы экзаменов", "group": "Справочники", "fields": {
        "id": "ID типа экзамена", "name": "Тип экзамена"}},
    "education_levels": {"title": "Уровни образования педагогов", "group": "Справочники", "fields": {
        "id": "ID уровня образования", "name": "Уровень образования"}},
    "qualification_levels": {"title": "Квалификационные категории", "group": "Справочники", "fields": {
        "id": "ID квалификационной категории", "name": "Категория"}},
    "class_profiles": {"title": "Профили классов", "group": "Справочники", "fields": {
        "id": "ID профиля класса", "name": "Профиль класса"}},
    "admission_profiles": {"title": "Направления поступления", "group": "Справочники", "fields": {
        "id": "ID направления поступления", "name": "Направление"}},
    "vw_school_dashboard": {"title": "Сводка по школам", "group": "Сводные таблицы", "fields": {
        "school_id": "ID школы", "school_name": "Наименование школы", "municipality": "Территория",
        "location": "Населённый пункт", "address": "Адрес", "students_count": "Количество учащихся",
        "teachers_count": "Количество педагогов", "classrooms_count": "Количество кабинетов",
        "has_library": "Есть библиотека", "has_gym": "Есть спортивный зал",
        "has_wifi": "Есть Wi-Fi", "rating_2025_2026": "Место в рейтинге 2025/2026"}},
    "vw_municipality_dashboard": {"title": "Сводка по территориям", "group": "Сводные таблицы", "fields": {
        "municipality_id": "ID территории", "municipality": "Территория",
        "population": "Население (демо)", "school_age_population": "Население школьного возраста (демо)",
        "schools_in_demo": "Количество школ (демо)", "students_in_demo": "Количество учащихся (демо)",
        "teachers_in_demo": "Количество педагогов (демо)"}},
    "vw_exam_dashboard": {"title": "Сводка по экзаменам", "group": "Сводные таблицы", "fields": {
        "academic_year": "Учебный год", "municipality": "Территория", "school": "Школа",
        "exam_type": "Тип экзамена", "subject": "Предмет",
        "classes_count": "Количество классов", "participants_count": "Количество сдававших",
        "weighted_average_score": "Средневзвешенный балл", "weighted_pass_percent": "Доля сдавших, %"}},
}

GROUPS = ("Школы и обучение", "Результаты и достижения", "Справочники", "Сводные таблицы")

# Вычисляемые читаемые подписи связанных записей. Только чтение, без замены ID.
CLASS_TITLE = """(SELECT c.grade_number::text || c.class_letter || ' — ' || s.name || ' (' || y.name || ')'
FROM edu_khv.classes c
JOIN edu_khv.schools s ON s.id = c.school_id
JOIN edu_khv.academic_years y ON y.id = c.academic_year_id
WHERE c.id = t.class_id)"""
GRAD_TITLE = """(SELECT c.grade_number::text || c.class_letter || ' — ' || s.name || ' (' || y.name || ')'
FROM edu_khv.graduates g
JOIN edu_khv.classes c ON c.id = g.class_id
JOIN edu_khv.schools s ON s.id = c.school_id
JOIN edu_khv.academic_years y ON y.id = c.academic_year_id
WHERE g.id = t.graduate_id)"""

REFERENCE_COLUMNS = {
    "schools": {"municipality_id": ("municipalities", "Территория")},
    "school_infrastructure": {"school_id": ("schools", "Школа")},
    "teachers": {"school_id": ("schools", "Школа"),
                 "qualification_level_id": ("qualification_levels", "Квалификационная категория"),
                 "subject_id": ("subjects", "Предмет"),
                 "education_level_id": ("education_levels", "Уровень образования")},
    "classes": {"school_id": ("schools", "Школа"),
                "academic_year_id": ("academic_years", "Учебный год"),
                "class_profile_id": ("class_profiles", "Профиль класса")},
    "class_student_stats": {"class_id": (None, "Класс")},
    "graduates": {"class_id": (None, "Класс")},
    "graduate_admissions": {"graduate_id": (None, "Выпуск"),
                            "admission_profile_id": ("admission_profiles", "Направление поступления")},
    "exam_results": {"class_id": (None, "Класс"),
                     "exam_type_id": ("exam_types", "Тип экзамена"),
                     "subject_id": ("subjects", "Предмет")},
    "school_ratings": {"school_id": ("schools", "Школа"),
                       "academic_year_id": ("academic_years", "Учебный год")},
    "olympiads": {"school_id": ("schools", "Школа"),
                  "academic_year_id": ("academic_years", "Учебный год"),
                  "subject_id": ("subjects", "Предмет")},
}

DIRECT_SCHOOL_TABLES = {"school_infrastructure", "teachers", "classes", "school_ratings", "olympiads"}
CLASS_SCHOOL_TABLES = {"class_student_stats", "graduates", "exam_results"}
DIRECT_YEAR_TABLES = {"classes", "school_ratings", "olympiads"}
CLASS_YEAR_TABLES = {"class_student_stats", "graduates", "exam_results"}


@st.cache_resource(show_spinner=False)
def db_engine():
    """Настройки из DATABASE_URL либо переменных DB_*, либо secrets Streamlit."""
    cfg = {}
    try:
        cfg = dict(st.secrets)
    except Exception:
        cfg = {}
    url = os.getenv("DATABASE_URL") or cfg.get("DATABASE_URL")
    if url:
        url = str(url)
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return create_engine(url, pool_pre_ping=True, pool_recycle=1800)

    def setting(name: str, default: str = "") -> str:
        return str(os.getenv(name) or cfg.get(name) or default)

    host = setting("DB_HOST")
    user = setting("DB_USER")
    password = setting("DB_PASSWORD")
    database = setting("DB_NAME")
    if not (host and user and database):
        raise ValueError("Не настроено подключение. Укажите DATABASE_URL или DB_HOST, DB_USER, DB_NAME и DB_PASSWORD.")
    sslmode = setting("DB_SSLMODE")
    connection_url = URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=host,
        port=int(setting("DB_PORT", "5432")),
        database=database,
        query={"sslmode": sslmode} if sslmode else {},
    )
    return create_engine(connection_url, pool_pre_ping=True, pool_recycle=1800)


@st.cache_data(ttl=120, show_spinner=False)
def query(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with db_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def fetch_scalar(sql: str, params: dict[str, Any] | None = None) -> int:
    data = query(sql, params)
    return int(data.iloc[0, 0]) if not data.empty else 0


def pretty(df: pd.DataFrame, table: str) -> pd.DataFrame:
    result = df.rename(columns=TABLES[table]["fields"]).copy()
    for col in result.columns:
        # В SQL NULL сохраняются как пустые значения, boolean показываем на русском.
        if pd.api.types.is_bool_dtype(result[col]):
            result[col] = result[col].map({True: "Да", False: "Нет"})
        elif result[col].dtype == "object" and result[col].dropna().map(lambda v: isinstance(v, bool)).all() and not result[col].dropna().empty:
            result[col] = result[col].map({True: "Да", False: "Нет"})
        if col in {"Дата начала", "Дата окончания"}:
            result[col] = pd.to_datetime(result[col], errors="coerce").dt.strftime("%d.%m.%Y")
    return result


def extra_expressions(table: str) -> list[str]:
    expressions = []
    for column, (referenced_table, label) in REFERENCE_COLUMNS.get(table, {}).items():
        if referenced_table is None:
            expr = GRAD_TITLE if column == "graduate_id" else CLASS_TITLE
        else:
            expr = f'(SELECT r.name FROM edu_khv."{referenced_table}" r WHERE r.id = t."{column}")'
        expressions.append(f'{expr} AS "{label}"')
    return expressions


def school_id_expression(table: str) -> str | None:
    if table == "schools":
        return "t.id"
    if table in DIRECT_SCHOOL_TABLES:
        return "t.school_id"
    if table in CLASS_SCHOOL_TABLES:
        return "(SELECT c.school_id FROM edu_khv.classes c WHERE c.id = t.class_id)"
    if table == "graduate_admissions":
        return "(SELECT c.school_id FROM edu_khv.graduates g JOIN edu_khv.classes c ON c.id = g.class_id WHERE g.id = t.graduate_id)"
    if table == "vw_school_dashboard":
        return "t.school_id"
    if table == "vw_exam_dashboard":
        # Представление содержит имя школы, но не её ID; учитываем также территорию.
        return "(SELECT s.id FROM edu_khv.schools s JOIN edu_khv.municipalities m ON m.id = s.municipality_id WHERE s.name = t.school AND m.name = t.municipality LIMIT 1)"
    return None


def year_id_expression(table: str) -> str | None:
    if table in DIRECT_YEAR_TABLES:
        return "t.academic_year_id"
    if table in CLASS_YEAR_TABLES:
        return "(SELECT c.academic_year_id FROM edu_khv.classes c WHERE c.id = t.class_id)"
    if table == "graduate_admissions":
        return "(SELECT c.academic_year_id FROM edu_khv.graduates g JOIN edu_khv.classes c ON c.id = g.class_id WHERE g.id = t.graduate_id)"
    return None


def make_where(table: str, municipality_id: int | None, school_id: int | None,
               year_id: int | None, year_name: str | None, find: str) -> tuple[str, dict[str, Any]]:
    conditions: list[str] = []
    params: dict[str, Any] = {}
    school_expr = school_id_expression(table)
    if municipality_id is not None:
        if table == "municipalities":
            conditions.append("t.id = :municipality_id")
        elif table == "vw_municipality_dashboard":
            conditions.append("t.municipality_id = :municipality_id")
        elif table in ("vw_school_dashboard", "vw_exam_dashboard"):
            conditions.append("t.municipality = (SELECT name FROM edu_khv.municipalities WHERE id = :municipality_id)")
        elif school_expr is not None:
            conditions.append(f"EXISTS (SELECT 1 FROM edu_khv.schools f WHERE f.id = {school_expr} AND f.municipality_id = :municipality_id)")
        params["municipality_id"] = municipality_id
    if school_id is not None and school_expr is not None:
        conditions.append(f"{school_expr} = :school_id")
        params["school_id"] = school_id

    year_expr = year_id_expression(table)
    if year_id is not None and year_expr is not None:
        conditions.append(f"{year_expr} = :year_id")
        params["year_id"] = year_id
    elif year_name and table == "vw_exam_dashboard":
        conditions.append("t.academic_year = :year_name")
        params["year_name"] = year_name

    if find.strip():
        search_exprs = [f'CAST(t."{c}" AS TEXT)' for c in TABLES[table]["fields"]]
        # Поиск также по расшифровкам внешних ключей (например, названию школы).
        search_exprs += [
            f"CAST({full_expr.rsplit(' AS ', 1)[0]} AS TEXT)"
            for full_expr in extra_expressions(table)
        ]
        conditions.append("(" + " OR ".join(f"{expr} ILIKE :find" for expr in search_exprs) + ")")
        params["find"] = "%" + find.strip().replace("%", "\\%").replace("_", "\\_") + "%"
    return (" WHERE " + " AND ".join(conditions) if conditions else ""), params


def frame_table(table: str, where: str, params: dict[str, Any], limit: int, offset: int) -> pd.DataFrame:
    extras = extra_expressions(table)
    selects = "t.*" + (", " + ", ".join(extras) if extras else "")
    order = {
        "vw_school_dashboard": 't.school_id',
        "vw_municipality_dashboard": 't.municipality_id',
        "vw_exam_dashboard": 't.academic_year DESC, t.municipality, t.school, t.exam_type, t.subject',
    }.get(table, "t.id")
    sql = f'SELECT {selects} FROM edu_khv."{table}" t {where} ORDER BY {order} LIMIT :limit OFFSET :offset'
    return pretty(query(sql, {**params, "limit": limit, "offset": offset}), table)


def render_overview(municipalities: pd.DataFrame):
    st.subheader("Общая сводка")
    st.caption("Показатели рассчитаны по демонстрационной базе, а не по официальной статистике Хабаровского края.")
    region_options = {"Все территории": None}
    region_options.update({row["name"]: int(row["id"]) for _, row in municipalities.iterrows()})
    selected_region = st.selectbox("Территория", list(region_options), key="overview_region")
    m_id = region_options[selected_region]
    where = "WHERE municipality_id = :id" if m_id else ""
    params = {"id": m_id} if m_id else {}
    school_summary = query(f"""SELECT COALESCE(SUM(schools_in_demo),0)::integer AS schools,
      COALESCE(SUM(students_in_demo),0)::integer AS students,
      COALESCE(SUM(teachers_in_demo),0)::integer AS teachers,
      COUNT(*)::integer AS municipalities
      FROM edu_khv.vw_municipality_dashboard {where}""", params).iloc[0]
    cols = st.columns(4)
    cards = (
        ("Школ", "schools"), ("Учащихся", "students"),
        ("Педагогов", "teachers"), ("Территорий", "municipalities"),
    )
    for col, (label, field) in zip(cols, cards):
        col.metric(label, f"{int(school_summary[field]):,}".replace(",", " "))

    st.markdown("#### Сравнение территорий")
    summary = query(f"""SELECT municipality AS "Территория", schools_in_demo AS "Школ",
      students_in_demo AS "Учащихся", teachers_in_demo AS "Педагогов"
      FROM edu_khv.vw_municipality_dashboard {where}
      ORDER BY students_in_demo DESC""", params)
    if len(summary):
        metric = st.selectbox("Показатель", ["Учащихся", "Педагогов", "Школ"], key="overview_metric")
        st.bar_chart(summary.set_index("Территория")[[metric]], horizontal=True, x_label=metric, y_label="Территория")
        with st.expander("Показать числовую таблицу"):
            st.dataframe(summary, hide_index=True, use_container_width=True)
    st.markdown("#### Школы и основные показатели")
    school_where = "WHERE m.id = :id" if m_id else ""
    school_rows = query(f"""SELECT s.name AS "Школа", m.name AS "Территория",
          s.students_count AS "Учащихся", s.teachers_count AS "Педагогов",
          i.classrooms_count AS "Кабинетов", r.ranking_place AS "Место в рейтинге"
        FROM edu_khv.schools s
        JOIN edu_khv.municipalities m ON m.id = s.municipality_id
        LEFT JOIN edu_khv.school_infrastructure i ON i.school_id = s.id
        LEFT JOIN edu_khv.school_ratings r ON r.school_id = s.id
          AND r.academic_year_id = (SELECT id FROM edu_khv.academic_years WHERE name = '2025/2026')
        {school_where} ORDER BY s.students_count DESC LIMIT 15""", params)
    st.dataframe(school_rows, hide_index=True, use_container_width=True)
    st.caption("Численность учащихся по школам относится к 2025/2026 учебному году; остальные данные также демонстрационные.")


def render_exams(municipalities: pd.DataFrame, years: pd.DataFrame):
    st.subheader("Анализ результатов экзаменов")
    first, second, third = st.columns(3)
    with first:
        year_name = st.selectbox("Учебный год", list(years["name"])[::-1], key="exam_year")
    with second:
        region_names = ["Все территории"] + list(municipalities["name"])
        region_name = st.selectbox("Территория", region_names, key="exam_region")
    with third:
        exam_type = st.selectbox("Тип экзамена", ["ЕГЭ", "ОГЭ"], key="exam_type")
    conditions = ["academic_year = :year", "exam_type = :exam_type"]
    params: dict[str, Any] = {"year": year_name, "exam_type": exam_type}
    if region_name != "Все территории":
        conditions.append("municipality = :region")
        params["region"] = region_name
    where = " AND ".join(conditions)
    data = query(f"""SELECT subject AS "Предмет",
       SUM(participants_count)::integer AS "Сдававших",
       ROUND((SUM(weighted_average_score * participants_count)
         / NULLIF(SUM(participants_count), 0))::numeric, 2) AS "Средний балл",
       ROUND((SUM(weighted_pass_percent * participants_count)
         / NULLIF(SUM(participants_count), 0))::numeric, 2) AS "Доля сдавших, %"
       FROM edu_khv.vw_exam_dashboard
       WHERE {where}
       GROUP BY subject ORDER BY subject""", params)
    if data.empty:
        st.info("По выбранным параметрам записей нет.")
        return
    st.info("ОГЭ и ЕГЭ отображаются отдельно: у них разные шкалы оценивания. Данные вымышлены.")
    st.markdown("#### Средний балл по предметам")
    chart = data.copy()
    chart["Средний балл"] = pd.to_numeric(chart["Средний балл"])
    st.bar_chart(chart.set_index("Предмет")[["Средний балл"]], horizontal=True, x_label="Средний балл", y_label="Предмет")
    st.markdown("#### Подробные результаты")
    st.dataframe(data, hide_index=True, use_container_width=True)
    st.download_button("Скачать результаты (CSV)", data.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name="экзамены_хабаровский_край.csv", mime="text/csv")


def render_tables(municipalities: pd.DataFrame, years: pd.DataFrame):
    st.subheader("Просмотр таблиц базы данных")
    group = st.selectbox("Группа таблиц", GROUPS)
    visible = [(k, v["title"]) for k, v in TABLES.items() if v["group"] == group]
    choice = st.selectbox("Таблица", [v[0] for v in visible], format_func=lambda key: TABLES[key]["title"])
    st.caption("Названия полей и связанных справочников отображаются на русском языке. Изменение записей отключено.")

    applicable_region = choice == "municipalities" or choice in ("vw_school_dashboard", "vw_municipality_dashboard", "vw_exam_dashboard") or school_id_expression(choice) is not None
    applicable_school = school_id_expression(choice) is not None
    applicable_year = year_id_expression(choice) is not None or choice == "vw_exam_dashboard"

    top_cols = st.columns(3)
    m_id: int | None = None
    school_id: int | None = None
    year_id: int | None = None
    year_name: str | None = None
    with top_cols[0]:
        if applicable_region:
            territory_options = {"Все территории": None}
            territory_options.update({r["name"]: int(r["id"]) for _, r in municipalities.iterrows()})
            selected = st.selectbox("Территория", list(territory_options), key=f"territory_{choice}")
            m_id = territory_options[selected]
    with top_cols[1]:
        if applicable_school:
            if m_id is not None:
                school_rows = query("SELECT id, name FROM edu_khv.schools WHERE municipality_id = :id ORDER BY name", {"id": m_id})
            else:
                school_rows = query("SELECT id, name FROM edu_khv.schools ORDER BY name")
            choices = {"Все школы": None}
            choices.update({f'{r["name"]} (ID {r["id"]})': int(r["id"]) for _, r in school_rows.iterrows()})
            selected_school = st.selectbox("Школа", list(choices), key=f"school_{choice}")
            school_id = choices[selected_school]
    with top_cols[2]:
        if applicable_year:
            year_options = {"Все учебные годы": (None, None)}
            year_options.update({r["name"]: (int(r["id"]), r["name"]) for _, r in years.iterrows()})
            year_choice = st.selectbox("Учебный год", list(year_options), key=f"year_{choice}")
            year_id, year_name = year_options[year_choice]

    q1, q2 = st.columns([3, 1])
    with q1:
        find = st.text_input("Поиск по значениям полей", placeholder="Например: Хабаровск, 2025, 11...", key=f"find_{choice}")
    with q2:
        page_size = st.selectbox("Строк на странице", [25, 50, 100, 250, 500], index=2)

    where, params = make_where(choice, m_id, school_id, year_id, year_name, find)
    try:
        total = fetch_scalar(f'SELECT COUNT(*) FROM edu_khv."{choice}" t {where}', params)
        pages = max(1, math.ceil(total / page_size))
        c1, c2 = st.columns([2, 1])
        c1.caption(f"Найдено записей: {total:,}".replace(",", " "))
        with c2:
            page = st.number_input("Страница", min_value=1, max_value=pages, value=1, step=1, key=f"page_{choice}")
        page_data = frame_table(choice, where, params, page_size, (page - 1) * page_size)
        if page_data.empty:
            st.info("Записей с указанными фильтрами нет.")
        else:
            st.dataframe(page_data, hide_index=True, use_container_width=True, height=min(660, max(220, len(page_data) * 36 + 42)))
        with st.expander("Экспорт CSV"):
            max_export = 20000
            st.caption(f"Экспортируются все строки с выбранными фильтрами (не более {max_export:,}); названия столбцов на русском. Файл в UTF-8 с BOM.".replace(",", " "))
            export_data = frame_table(choice, where, params, max_export, 0)
            st.download_button("Скачать CSV", export_data.to_csv(index=False, sep=";").encode("utf-8-sig"),
                               file_name=f"{choice}.csv", mime="text/csv", key=f"download_{choice}")
    except Exception as exc:
        st.error("Не удалось загрузить данные выбранной таблицы. Проверьте наличие таблицы и права пользователя PostgreSQL.")
        st.caption(f"Техническая информация: {type(exc).__name__}: {str(exc).splitlines()[0][:200]}")


st.markdown("""
<style>
.block-container { padding-top: 1.8rem; }
[data-testid="stMetric"] { border: 1px solid rgba(128,128,128,.18); border-radius: 12px; padding: 14px 18px; }
[data-testid="stSidebar"] h1 { font-size: 1.15rem; }
</style>
""", unsafe_allow_html=True)

st.title("Образование Хабаровского края")
st.caption("Демонстрационная система мониторинга школ и образовательных показателей")

with st.sidebar:
    st.markdown("### Разделы")
    page = st.radio("Навигация", ["Обзор", "Таблицы базы данных", "Результаты экзаменов"], label_visibility="collapsed")
    st.divider()
    st.caption("18 таблиц · 3 представления · PostgreSQL")
    if st.button("Обновить данные", use_container_width=True):
        query.clear()
        st.rerun()
    st.caption("Данные синтетические. Не официальная статистика.")

try:
    # Запросы сразу выявляют ошибки конфигурации или отсутствие схемы.
    municipalities_df = query("SELECT id, name FROM edu_khv.municipalities ORDER BY name")
    years_df = query("SELECT id, name FROM edu_khv.academic_years ORDER BY start_date")
except Exception as exc:
    st.error("Не удалось подключиться к PostgreSQL или найти схему edu_khv.")
    st.info("Сначала импортируйте файл sql/khabarovsk_education_demo.sql, затем настройте подключение через DATABASE_URL или .streamlit/secrets.toml.")
    st.caption(f"Техническая информация: {type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
    st.stop()

if page == "Обзор":
    render_overview(municipalities_df)
elif page == "Таблицы базы данных":
    render_tables(municipalities_df, years_df)
else:
    render_exams(municipalities_df, years_df)
