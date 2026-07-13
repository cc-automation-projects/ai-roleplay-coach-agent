# UI Reference — AI Roleplay Coach

Каталог экранов фронтенда. Каждая страница — готовый HTML-макет с Tailwind CSS. Откройте файл в браузере для просмотра.

---

## 🔐 Авторизация

| Экран | Файл | Описание |
|-------|------|----------|
| Вход | [`login.html`](./ui/login.html) | Форма входа с выбором роли (Оператор/Тренер/Админ) |
| Регистрация | [`register.html`](./ui/register.html) | Форма регистрации нового пользователя |

---

## 👤 Оператор

| Экран | Файл | Описание |
|-------|------|----------|
| Дашборд оператора | [`dashboard-operator.html`](./ui/dashboard-operator.html) | Главный экран: выбор сценария, XP, прогресс, задания |
| Симуляция | [`simulation.html`](./ui/simulation.html) | Чат-тренажёр: диалог с AI-клиентом, живые подсказки, DDA, метрики |
| Результаты сессии | [`results.html`](./ui/results.html) | Разбор диалога: Sandwich feedback, радар навыков, XP, бейджи |
| Квиз | [`quiz.html`](./ui/quiz.html) | Прохождение теста с вариантами ответов |

---

## 🧑‍🏫 Тренер / Супервайзер

| Экран | Файл | Описание |
|-------|------|----------|
| Дашборд тренера | [`dashboard-trainer.html`](./ui/dashboard-trainer.html) | Аналитика: сводки, распределение оценок, отстающие, тренды |
| Учебный план | [`learning-plan.html`](./ui/learning-plan.html) | Индивидуальный план обучения, квизы, прогресс |
| Fairness-аудит | [`fairness.html`](./ui/fairness.html) | Метрики справедливости: Demographic Parity, Equal Opportunity и др. |

---

## ⚙️ Администратор

| Экран | Файл | Описание |
|-------|------|----------|
| Админ-панель | [`admin.html`](./ui/admin.html) | Управление пользователями, сценариями, ролями, LMS Sync, Health мониторинг |

---

## Карта соответствия документации

| Страница | Подробное описание в документах |
|----------|--------------------------------|
| Login / Register | [`USER_GUIDE.md`](USER_GUIDE.md) — разделы 2.1–2.2 |
| Dashboard Operator | [`USER_GUIDE.md`](USER_GUIDE.md) — раздел 5.1 |
| Simulation | [`USER_GUIDE.md`](USER_GUIDE.md) — раздел 3 |
| Results | [`USER_GUIDE.md`](USER_GUIDE.md) — раздел 3.3 |
| Dashboard Trainer | [`USER_GUIDE.md`](USER_GUIDE.md) — раздел 5.2 |
| Learning Plan | [`USER_GUIDE.md`](USER_GUIDE.md) — раздел 4.3 |
| Fairness | [`INTEGRATION_TEST_SPEC.md`](INTEGRATION_TEST_SPEC.md), [`SOURCE_CODE_REFERENCE.md`](SOURCE_CODE_REFERENCE.md) |
| Admin Panel | [`ADMIN_GUIDE.md`](ADMIN_GUIDE.md), [`DEPLOYMENT_PLAN.md`](DEPLOYMENT_PLAN.md) |
