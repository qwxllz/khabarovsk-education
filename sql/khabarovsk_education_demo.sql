-- PostgreSQL 14+. Полностью СИНТЕТИЧЕСКИЕ демонстрационные данные.
-- Структура основана на схеме пользователя, названия организаций и показатели вымышлены.
-- ВНИМАНИЕ: повторный запуск УДАЛИТ схему edu_khv и все данные внутри нее.
BEGIN;
DROP SCHEMA IF EXISTS edu_khv CASCADE;
CREATE SCHEMA edu_khv;
SET LOCAL search_path TO edu_khv, public;

-- 1. Справочники
CREATE TABLE municipalities (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    administrative_center text NOT NULL,
    population integer NOT NULL CHECK (population >= 0),
    school_age_population integer NOT NULL CHECK (school_age_population >= 0 AND school_age_population <= population)
);
CREATE TABLE academic_years (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    start_date date NOT NULL,
    end_date date NOT NULL,
    CHECK (end_date > start_date)
);
CREATE TABLE subjects (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE exam_types (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE education_levels (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE qualification_levels (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE class_profiles (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);
CREATE TABLE admission_profiles (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);

-- 2. Основные сущности
CREATE TABLE schools (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    municipality_id integer NOT NULL REFERENCES municipalities(id),
    name text NOT NULL,
    address text NOT NULL,
    students_count integer NOT NULL DEFAULT 0 CHECK (students_count >= 0),
    location text NOT NULL,
    teachers_count integer NOT NULL DEFAULT 0 CHECK (teachers_count >= 0),
    UNIQUE (municipality_id, name)
);
CREATE TABLE school_infrastructure (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    school_id integer NOT NULL UNIQUE REFERENCES schools(id) ON DELETE CASCADE,
    classrooms_count integer NOT NULL CHECK (classrooms_count > 0),
    school_buses_count integer NOT NULL CHECK (school_buses_count >= 0),
    has_library boolean NOT NULL,
    has_life_safety_classroom boolean NOT NULL,
    has_computer_class boolean NOT NULL,
    has_gym boolean NOT NULL,
    has_canteen boolean NOT NULL,
    has_sports_ground boolean NOT NULL,
    has_accessible_environment boolean NOT NULL,
    has_medical_room boolean NOT NULL,
    has_swimming_pool boolean NOT NULL,
    has_growth_center boolean NOT NULL,
    medical_staff_count integer NOT NULL CHECK (medical_staff_count >= 0),
    has_wifi boolean NOT NULL,
    computers_count integer NOT NULL CHECK (computers_count >= 0)
);
CREATE TABLE teachers (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    school_id integer NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    average_experience_years numeric(4,1) NOT NULL CHECK (average_experience_years >= 0),
    qualification_level_id integer NOT NULL REFERENCES qualification_levels(id),
    weekly_load_hours integer NOT NULL CHECK (weekly_load_hours BETWEEN 1 AND 60),
    subject_id integer NOT NULL REFERENCES subjects(id),
    has_additional_training boolean NOT NULL,
    education_level_id integer NOT NULL REFERENCES education_levels(id)
);
CREATE TABLE classes (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    school_id integer NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id integer NOT NULL REFERENCES academic_years(id),
    class_profile_id integer NOT NULL REFERENCES class_profiles(id),
    grade_number integer NOT NULL CHECK (grade_number BETWEEN 1 AND 11),
    class_letter text NOT NULL CHECK (class_letter IN ('А', 'Б', 'В')),
    is_graduating boolean NOT NULL,
    students_count integer NOT NULL CHECK (students_count BETWEEN 1 AND 45),
    UNIQUE (school_id, academic_year_id, grade_number, class_letter),
    CHECK (is_graduating = (grade_number IN (9, 11)))
);
CREATE TABLE class_student_stats (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id integer NOT NULL UNIQUE REFERENCES classes(id) ON DELETE CASCADE,
    immigrant_students_count integer NOT NULL CHECK (immigrant_students_count >= 0),
    repeaters_count integer NOT NULL CHECK (repeaters_count >= 0)
);
CREATE TABLE graduates (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id integer NOT NULL UNIQUE REFERENCES classes(id) ON DELETE CASCADE,
    graduates_count integer NOT NULL CHECK (graduates_count >= 0),
    honors_count integer NOT NULL CHECK (honors_count >= 0),
    medalists_count integer NOT NULL CHECK (medalists_count >= 0),
    certificates_received integer NOT NULL CHECK (certificates_received >= 0),
    certificates_not_received integer NOT NULL CHECK (certificates_not_received >= 0),
    CHECK (honors_count <= graduates_count),
    CHECK (medalists_count <= honors_count),
    CHECK (certificates_received + certificates_not_received = graduates_count)
);
CREATE TABLE graduate_admissions (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graduate_id integer NOT NULL REFERENCES graduates(id) ON DELETE CASCADE,
    admission_profile_id integer NOT NULL REFERENCES admission_profiles(id),
    admitted_count integer NOT NULL CHECK (admitted_count >= 0),
    khabarovsk_krai_percent numeric(5,2) NOT NULL CHECK (khabarovsk_krai_percent BETWEEN 0 AND 100),
    UNIQUE (graduate_id, admission_profile_id)
);
CREATE TABLE exam_results (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_id integer NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    exam_type_id integer NOT NULL REFERENCES exam_types(id),
    subject_id integer NOT NULL REFERENCES subjects(id),
    average_score numeric(5,2) NOT NULL CHECK (average_score BETWEEN 0 AND 100),
    participants_count integer NOT NULL CHECK (participants_count >= 0),
    passed_percent numeric(5,2) NOT NULL CHECK (passed_percent BETWEEN 0 AND 100),
    UNIQUE (class_id, exam_type_id, subject_id)
);
CREATE TABLE school_ratings (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    school_id integer NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id integer NOT NULL REFERENCES academic_years(id),
    ranking_place integer NOT NULL CHECK (ranking_place > 0),
    UNIQUE (school_id, academic_year_id),
    UNIQUE (academic_year_id, ranking_place)
);
CREATE TABLE olympiads (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    subject_id integer NOT NULL REFERENCES subjects(id),
    school_id integer NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id integer NOT NULL REFERENCES academic_years(id),
    result text NOT NULL CHECK (result IN ('Участник', 'Призёр', 'Победитель'))
);

-- 3. Справочные данные. Население и возрастная структура: вымышленные числа.
INSERT INTO municipalities (name, administrative_center, population, school_age_population) VALUES
('Город Хабаровск', 'Хабаровск', 620000, 94000),
('Город Комсомольск-на-Амуре', 'Комсомольск-на-Амуре', 245000, 37500),
('Амурский район', 'Амурск', 52000, 7600),
('Бикинский район', 'Бикин', 21000, 3100),
('Ванинский район', 'Ванино', 31000, 4650),
('Вяземский район', 'Вяземский', 19500, 2850),
('Район имени Лазо', 'Переяславка', 35500, 5100),
('Нанайский район', 'Троицкое', 13500, 1900),
('Николаевский район', 'Николаевск-на-Амуре', 24500, 3450),
('Советско-Гаванский район', 'Советская Гавань', 36500, 5250),
('Солнечный район', 'Солнечный', 26500, 3900),
('Ульчский район', 'Богородское', 14500, 2150);

INSERT INTO academic_years (name, start_date, end_date) VALUES
('2023/2024', '2023-09-01', '2024-08-31'),
('2024/2025', '2024-09-01', '2025-08-31'),
('2025/2026', '2025-09-01', '2026-08-31');

INSERT INTO subjects (name) VALUES
('Русский язык'), ('Математика'), ('Литература'),
('История'), ('Обществознание'), ('Физика'),
('Химия'), ('Биология'), ('География'),
('Информатика'), ('Английский язык'), ('Физическая культура');

INSERT INTO exam_types (name) VALUES ('ОГЭ'), ('ЕГЭ');
INSERT INTO education_levels (name) VALUES
('Среднее профессиональное'), ('Высшее образование'), ('Магистратура');
INSERT INTO qualification_levels (name) VALUES
('Без категории'), ('Первая категория'), ('Высшая категория');
INSERT INTO class_profiles (name) VALUES
('Общеобразовательный'), ('Физико-математический'),
('Гуманитарный'), ('Естественно-научный'), ('Информационно-технологический');
INSERT INTO admission_profiles (name) VALUES
('10 класс'), ('СПО: колледж или техникум'),
('Высшее образование: вуз'), ('Другое направление');

-- 4. 60 ВЫМЫШЛЕННЫХ школ: по 5 на каждую территорию.
INSERT INTO schools (municipality_id, name, address, location)
SELECT m.id,
       format('Демонстрационная школа №%s', (m.id - 1) * 5 + n.n),
       format('%s, ул. Учебная, д. %s (условный адрес)', m.administrative_center, 2 * n.n + m.id),
       m.administrative_center
FROM municipalities m
CROSS JOIN generate_series(1, 5) AS n(n)
ORDER BY m.id, n.n;

-- 5. Инфраструктура каждой школы.
INSERT INTO school_infrastructure (
    school_id, classrooms_count, school_buses_count,
    has_library, has_life_safety_classroom, has_computer_class,
    has_gym, has_canteen, has_sports_ground, has_accessible_environment,
    has_medical_room, has_swimming_pool, has_growth_center,
    medical_staff_count, has_wifi, computers_count
)
SELECT s.id, 15 + (s.id % 30), s.id % 4,
       s.id % 11 <> 0, s.id % 6 <> 0, true, s.id % 9 <> 0,
       s.id % 13 <> 0, s.id % 4 <> 0, s.id % 3 <> 0,
       s.id % 8 <> 0, s.id % 15 = 0, s.id % 5 = 0,
       1 + s.id % 3, s.id % 7 <> 0,
       12 + (s.id * 7 % 95)
FROM schools s;

-- 6. Преподаватели: от 17 до 26 условных записей на школу.
INSERT INTO teachers (
    school_id, average_experience_years, qualification_level_id,
    weekly_load_hours, subject_id, has_additional_training, education_level_id
)
SELECT s.id,
       (2 + (s.id * 3 + t.n * 5) % 30)::numeric(4,1),
       1 + (s.id + t.n) % 3,
       18 + (s.id + t.n * 3) % 19,
       1 + (s.id + t.n) % 12,
       (s.id + t.n) % 4 <> 0,
       CASE WHEN (s.id + t.n) % 12 = 0 THEN 1
            WHEN (s.id + t.n) % 17 = 0 THEN 3 ELSE 2 END
FROM schools s
CROSS JOIN LATERAL generate_series(1, 17 + s.id % 10) AS t(n);

-- 7. Классы за 3 учебных года; в части школ есть параллели А и Б.
-- Для каждого года создаются все классы с 1-го по 11-й.
INSERT INTO classes (
    school_id, academic_year_id, class_profile_id,
    grade_number, class_letter, is_graduating, students_count
)
SELECT s.id, y.id,
       CASE WHEN g.grade_number < 10 THEN 1
            ELSE 1 + ((s.id + y.id + p.n) % 5) END,
       g.grade_number,
       CASE WHEN p.n = 1 THEN 'А' ELSE 'Б' END,
       g.grade_number IN (9, 11),
       19 + ((s.id * 7 + y.id * 5 + g.grade_number * 3 + p.n) % 14)
FROM schools s
CROSS JOIN academic_years y
CROSS JOIN generate_series(1, 11) AS g(grade_number)
CROSS JOIN LATERAL generate_series(1, CASE WHEN s.id % 3 = 0 THEN 2 ELSE 1 END) AS p(n);

-- 8. Статистика учащихся класса.
INSERT INTO class_student_stats (class_id, immigrant_students_count, repeaters_count)
SELECT c.id,
       (c.id * 3 + c.grade_number) % 4,
       CASE WHEN c.id % 19 = 0 THEN 1 ELSE 0 END
FROM classes c;

-- 9. Выпускники только 9-х и 11-х классов.
INSERT INTO graduates (
    class_id, graduates_count, honors_count, medalists_count,
    certificates_received, certificates_not_received
)
SELECT c.id,
       c.students_count,
       c.id % 6,
       CASE WHEN c.grade_number = 11 THEN c.id % 3 ELSE 0 END,
       c.students_count - (c.id % 3),
       c.id % 3
FROM classes c
WHERE c.is_graduating;

-- 10. Поступление: 3 направления на каждый выпускной класс.
-- Доли считаются от получивших аттестат и не превышают их число.
INSERT INTO graduate_admissions (
    graduate_id, admission_profile_id, admitted_count, khabarovsk_krai_percent
)
SELECT g.id, ap.id,
       CASE
           WHEN c.grade_number = 9 AND ap.id = 1 THEN floor(g.certificates_received * 0.55)::integer
           WHEN c.grade_number = 9 AND ap.id = 2 THEN floor(g.certificates_received * 0.35)::integer
           WHEN c.grade_number = 9 AND ap.id = 4 THEN floor(g.certificates_received * 0.10)::integer
           WHEN c.grade_number = 11 AND ap.id = 3 THEN floor(g.certificates_received * 0.65)::integer
           WHEN c.grade_number = 11 AND ap.id = 2 THEN floor(g.certificates_received * 0.25)::integer
           WHEN c.grade_number = 11 AND ap.id = 4 THEN floor(g.certificates_received * 0.10)::integer
           ELSE 0
       END,
       (60 + (g.id * 3 + ap.id * 7) % 36)::numeric(5,2)
FROM graduates g
JOIN classes c ON c.id = g.class_id
JOIN admission_profiles ap ON (
     (c.grade_number = 9 AND ap.id IN (1, 2, 4))
  OR (c.grade_number = 11 AND ap.id IN (2, 3, 4))
);

-- 11. ОГЭ: русский, математика, обществознание.
-- ЕГЭ: русский, профильная математика, информатика.
INSERT INTO exam_results (
    class_id, exam_type_id, subject_id, average_score, participants_count, passed_percent
)
SELECT c.id, e.exam_type_id, e.subject_id,
       CASE WHEN e.exam_type_id = 1
            THEN (3.20 + ((c.id + e.subject_id * 3) % 17) * 0.09)::numeric(5,2)
            ELSE (52 + ((c.id * 7 + e.subject_id * 9) % 39))::numeric(5,2)
       END,
       GREATEST(1, c.students_count - (c.id + e.subject_id) % 4),
       (81 + ((c.id * 3 + e.subject_id * 5) % 20))::numeric(5,2)
FROM classes c
JOIN (
    VALUES (9, 1, 1), (9, 1, 2), (9, 1, 5),
           (11, 2, 1), (11, 2, 2), (11, 2, 10)
) AS e(grade_number, exam_type_id, subject_id)
    ON e.grade_number = c.grade_number;

-- 12. Рейтинг по каждому учебному году: места 1..60.
INSERT INTO school_ratings (school_id, academic_year_id, ranking_place)
SELECT s.id, y.id,
       row_number() OVER (
           PARTITION BY y.id
           ORDER BY (s.id * 37 + y.id * 17) % 101, s.id
       )::integer
FROM schools s
CROSS JOIN academic_years y;

-- 13. Олимпиады: 3 участия на школу за каждый учебный год.
INSERT INTO olympiads (name, subject_id, school_id, academic_year_id, result)
SELECT CASE k.n
           WHEN 1 THEN 'Школьный этап Всероссийской олимпиады школьников'
           WHEN 2 THEN 'Муниципальный этап Всероссийской олимпиады школьников'
           ELSE 'Региональная учебная олимпиада (демо)'
       END,
       1 + (s.id + k.n * 3) % 12,
       s.id, y.id,
       CASE WHEN (s.id + y.id + k.n) % 11 = 0 THEN 'Победитель'
            WHEN (s.id + y.id + k.n) % 4 = 0 THEN 'Призёр'
            ELSE 'Участник' END
FROM schools s
CROSS JOIN academic_years y
CROSS JOIN generate_series(1, 3) AS k(n);

-- 14. Актуальные показатели школы на 2025/2026 год.
UPDATE schools s
SET students_count = q.total_students
FROM (
    SELECT school_id, sum(students_count)::integer AS total_students
    FROM classes
    WHERE academic_year_id = (SELECT id FROM academic_years WHERE name = '2025/2026')
    GROUP BY school_id
) q
WHERE s.id = q.school_id;

UPDATE schools s
SET teachers_count = q.total_teachers
FROM (
    SELECT school_id, count(*)::integer AS total_teachers
    FROM teachers
    GROUP BY school_id
) q
WHERE s.id = q.school_id;

-- 15. Индексы для фильтров и таблиц интерфейса.
CREATE INDEX idx_schools_municipality ON schools(municipality_id);
CREATE INDEX idx_teachers_school ON teachers(school_id);
CREATE INDEX idx_teachers_subject ON teachers(subject_id);
CREATE INDEX idx_classes_school_year ON classes(school_id, academic_year_id);
CREATE INDEX idx_classes_grade ON classes(grade_number);
CREATE INDEX idx_exam_class ON exam_results(class_id);
CREATE INDEX idx_exam_subject ON exam_results(subject_id);
CREATE INDEX idx_olympiads_school_year ON olympiads(school_id, academic_year_id);
CREATE INDEX idx_ratings_year ON school_ratings(academic_year_id);
CREATE INDEX idx_admissions_graduate ON graduate_admissions(graduate_id);

-- 16. Удобные представления для дашборда.
CREATE VIEW vw_school_dashboard AS
SELECT s.id AS school_id,
       s.name AS school_name,
       m.name AS municipality,
       s.location,
       s.address,
       s.students_count,
       s.teachers_count,
       si.classrooms_count,
       si.has_library,
       si.has_gym,
       si.has_wifi,
       r.ranking_place AS rating_2025_2026
FROM schools s
JOIN municipalities m ON m.id = s.municipality_id
LEFT JOIN school_infrastructure si ON si.school_id = s.id
LEFT JOIN school_ratings r ON r.school_id = s.id
LEFT JOIN academic_years y ON y.id = r.academic_year_id
                         AND y.name = '2025/2026'
WHERE y.name = '2025/2026';

CREATE VIEW vw_municipality_dashboard AS
SELECT m.id AS municipality_id,
       m.name AS municipality,
       m.population,
       m.school_age_population,
       count(s.id)::integer AS schools_in_demo,
       coalesce(sum(s.students_count), 0)::integer AS students_in_demo,
       coalesce(sum(s.teachers_count), 0)::integer AS teachers_in_demo
FROM municipalities m
LEFT JOIN schools s ON s.municipality_id = m.id
GROUP BY m.id, m.name, m.population, m.school_age_population;

CREATE VIEW vw_exam_dashboard AS
SELECT y.name AS academic_year,
       m.name AS municipality,
       s.name AS school,
       et.name AS exam_type,
       sub.name AS subject,
       count(*)::integer AS classes_count,
       sum(er.participants_count)::integer AS participants_count,
       round(sum(er.average_score * er.participants_count)
          / nullif(sum(er.participants_count), 0), 2) AS weighted_average_score,
       round(sum(er.passed_percent * er.participants_count)
          / nullif(sum(er.participants_count), 0), 2) AS weighted_pass_percent
FROM exam_results er
JOIN classes c ON c.id = er.class_id
JOIN schools s ON s.id = c.school_id
JOIN municipalities m ON m.id = s.municipality_id
JOIN academic_years y ON y.id = c.academic_year_id
JOIN exam_types et ON et.id = er.exam_type_id
JOIN subjects sub ON sub.id = er.subject_id
GROUP BY y.name, m.name, s.name, et.name, sub.name;

COMMIT;

-- Контрольные запросы (запустить после импорта):
-- SELECT 'municipalities' AS entity, count(*) FROM edu_khv.municipalities
-- UNION ALL SELECT 'schools', count(*) FROM edu_khv.schools
-- UNION ALL SELECT 'teachers', count(*) FROM edu_khv.teachers
-- UNION ALL SELECT 'classes', count(*) FROM edu_khv.classes
-- UNION ALL SELECT 'graduates', count(*) FROM edu_khv.graduates
-- UNION ALL SELECT 'exam_results', count(*) FROM edu_khv.exam_results;
-- SELECT * FROM edu_khv.vw_school_dashboard LIMIT 15;
-- SELECT * FROM edu_khv.vw_municipality_dashboard;
-- SELECT * FROM edu_khv.vw_exam_dashboard LIMIT 15;
