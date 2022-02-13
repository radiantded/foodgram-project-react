# FOODGRAM

Онлайн-сервис, где пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд


## Стек технологий
- проект написан на Python с использованием веб-фреймворка Django.
- работа с изображениями - sorl-thumbnail, pillow
- развернут на сервере Яндекс.Облако - nginx, ginicorn
- база данны PostgreSQL
- автоматическое развертывание проекта - Docker, docker-compose
- система управления версиями - git

## Как запустить проект, используя Docker:

1) Клонируйте репозиторий с проектом:
```
git clone https://github.com/radiantded/foodgram-project-react

```

2) В директори проекта создайте файл .env, в котором пропишите следующие переменые окружения:

- SECRET_KEY
- SQL_DATABASE
- SQL_USER
- SQL_PASSWORD
- SQL_HOST
- SQL_PORT

3) С помощью Dockerfile и docker-compose.yaml разверните проект:

```
docker-compose up --build

```

4) В новом окне терминала узнайте id контейнера foodgram_web и войдите в контейнер:

```
docker container ls

```

```
docker exec -it <CONTAINER_ID> bash

```

5) В контейнере выполните миграци, создайте суперпользователя:

```
python manage.py migrate

python manage.py createsuperuser

```
http://51.250.13.137/
admin
admin