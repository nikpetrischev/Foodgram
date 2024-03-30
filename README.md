# Проект Foodgram
[![Main Foodgram workflow](https://github.com/nikpetrischev/foodgram-project-react/actions/workflows/main.yml/badge.svg?branch=master&event=status)](https://github.com/nikpetrischev/foodgram-project-react/actions/workflows/main.yml)
  
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)




Foodgram реализован для публикации рецептов. Авторизованные пользователи
могут подписываться на понравившихся авторов, добавлять рецепты в избранное,
в покупки, скачать список покупок ингредиентов для добавленных в покупки
рецептов.

## Подготовка и запуск проекта
### Склонировать репозиторий на локальную машину:
```
git clone git@github.com:nikpetrischev/foodgram-project-react.git
```
## Для работы с удаленным сервером (на ubuntu):
* Выполните вход на свой удаленный сервер

* Установите docker на сервер:
  ```
  sudo apt install docker.io 
  ```
* Установите docker-compose на сервер:
  ```
  sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  ```
* Cоздайте .env файл и впишите:
  ```
  # django settings
  SECRET_KEY=<Секретный ключ из настроек Django>
  IS_DEBUG=<True/False>
  ALLOWED_HOSTS=<Список хостов через запятую>
  DB_PROD=<True/False>
  
  # postgresql
  POSTGRES_DB=foodgram_db
  POSTGRES_USER=<Имя пользователя для БД>
  POSTGRES_PASSWORD=<Пароль для БД>
  DB_HOST=<Хост для БД>
  DB_PORT=<Порт для БД. default:5432>
  ```
* Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
  ```
  HOST
  
  # Данные для Докера 
  DOCKER_USERNAME
  DOCKER_PASSWORD
  
  # Дaнные для работы БД
  POSTGRES_USER
  POSTGRES_PASSWORD
  
  # Данные для работы Django
  ALLOWED_HOSTS
  SECRET_KEY
  
  # Данные для подключения по ssh
  SSH_KEY
  SSH_PASSPHRASE
  USER
  ```
  Также в Variables добавьте переменные среды:
  ```
  DB_HOST
  DB_PORT
  DB_PROD
  POSTGRES_DB
  ```
  Структура Workflow выглядит следующим образом:
  ```
  tests >> Push backend image >> | >> deploy
                                 |
  Push frontend image   |  >>>>> |
  Push nginx image      |
  copy_files_to_server  |
  ```
* Чтобы создать суперпользователя Django на сервере:
  ```
  cd <ваш_путь_к_файлу_docker-comp[ose.yml>
  sudo docker compose exec backend python manage.py createsuperuser
  ```
