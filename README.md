# Руководство администратора по установке и эксплуатации веб-приложения "Мероприятус"
#### [Установка небходимых модулей](#Установка-необходимых-модулей)
#### [Установка веб-приложения](#Установка-веб-приложения)
#### [Настройка веб-приложения](#Настройка-веб-приложения)
#### [Запуск веб-приложения](#Запуск-веб-приложения)
# Установка необходимых модулей
Для работы веб приложения необходимо установить docker и docker compose
| № | Действие | Описание |
| --- | --- | --- |
| 1 | `sudo apt update` | Обновление пакетов |
| 2 | `sudo apt install ca-certificates curl gnupg` | Установка зависимостей |
| 3 | `sudo install -m 0755 -d /etc/apt/keyrings` | Добавление официального gpg ключа docker |
|  | `curl -fsSL https://download.docker.com/linux/ubuntu/gpg ` |  |
|  | `sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg` |  |
|  | `sudo chmod a+r /etc/apt/keyrings/docker.gpg` |  |
| 4 | `echo \ "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \ https://download.docker.com/linux/ubuntu \ $(. /etc/os-release && echo $VERSION_CODENAME) stable"` | Добавление репозитория docker |
|  | `sudo tee /etc/apt/sources.list.d/docker.list > /dev/null` |  |
| 5 | `sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin` | Установка docker и docker-compose |
| 6 | `docker compose version` | Проверка |
# Установка веб приложения
Просто клонируйте репозиторий в папку, где будете хранить веб-приложение\
`git clone https://github.com/ZogirderCMD/Meropriyatus.git`
# Настройка веб-приложения
После установки веб-приложения, откройте файл `.env`\
`sudo nano .env` \
`sudo vim .env` \
В данном файле вы можете настроить
| Переменная | Описание |
| --- | --- |
| POSTGRES_DB | Наименование базы данных |
| POSTGRES_USER | Пользователь базы данных |
| POSTGRES_PASSWORD | Пароль пользователя базы данных |
| POSTGRES_HOST | Хост базы данных в окружении контейнера (можно не менять) |
| POSTGRES_PORT | Порт базы данных |
# Запуск веб-приложения
Введите в терминале \
`sudo docker compose up --build -d` \
И ждите завершения запуска контейнера
