# Описание проекта Foodgram
Продуктовый помощник, сайт, который позволяет делиться рецептами со своими друзьями, 
следить за авторами, добавлять рецепты в избранное, а также составлять свой список покупок.
Проект работает на фреймворках Django и React.

## Деплой проекта на удалённый сервер

Если вы запуллите себе проект для дальнейших изменений, есть возможность настроить GitHub Workflow, для более удобного ведения разработки и деплоя.
Для этого необходимо в вашем репозитории настроить secret variables, которые приведены ниже.

```bash
DOCKER_PASSWORD - пароль от докера
DOCKER_USERNAME - логин от докера
HOST - ip удалённого сервера
SSH_KEY - SSH ключ удалённого сервера
SSH_PASSPHRASE - SSH пароль удалённого сервера
USER - user удалённого сервера
```

Подключаемся к серверу и устанавливаем Docker.

```bash
ssh username@ip
```

```bash
sudo apt update
```

```bash
sudo apt install curl
```

```bash
curl -fSL https://get.docker.com -o get-docker.sh
```

```bash
sudo sh ./get-docker.sh
```

```bash
sudo apt-get install docker-compose-plugin 
```

Создаём папку infra и переходим в неё:

```bash
mkdir infra
```

```bash
cd infra/
```

Создаём файлы docker-compose.yml, nginx.conf и .env в папке infra и переносим в них код из репозитория.

```bash
sudo nano docker-compose.yml
```

```bash
sudo nano nginx.conf
```

```bash
sudo nano .env
```

Пример заполнения файла .env

```python
DB_ENGINE=django.db.backends.postgresql
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY='django_secret_key'
DEBUG=False
ALLOWED_HOSTS=127.0.0.1 localhost server_ip server_domain
DB_NAME=foodgram
```

После заполнения файлов, выполняем команду:

```bash
docker-compose up -d
```
Создаём миграции, суперюзера и собираем статику для админ зоны.

```bash
sudo docker-compose exec backend python manage.py migrate
```

```bash
sudo docker-compose exec backend python manage.py createsuperuser
```

```bash
sudo docker-compose exec backend python manage.py collectstatic
```

Наполняем базу тегами и ингридиентами:

```bash
sudo docker-compose exec backend python manage.py loaddata data/tags.json --app recipes.tag
```

```bash
sudo docker-compose exec backend python manage.py load_data
```

Настройка и деплой выполнены, сайт готов к работе.


Пример проекта задеплоенного на сервер доступен по адресу:
https://foodgramproject.zapto.org/recipes

Для проверки админ зоны проекта был создан супер юзер, с данными которые предоставил ревьювер.

![Workflow Status](https://github.com/ripkrul/foodgram-project-react/actions/workflows/main.yml/badge.svg?branch=master&event=push)