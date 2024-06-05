import sqlite3
from sqlite3 import Error
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from html2image import Html2Image
from pprint import pprint
import re
import os


def extract_nonce(text):
    pattern = r'var filterHome = \{.*"nonce":"([^"]+)".*\}'

    # Поиск первого совпадения в тексте
    match = re.search(pattern, text)

    # Если совпадение найдено, возвращаем значение, иначе None
    if match:
        return match.group(1)
    else:
        return None


class DB:
    def __init__(self, db_file):
        """Инициализация соединения с базой данных SQLite"""
        self.connection = None
        self.db_file = db_file
        try:
            self.connection = sqlite3.connect(db_file, check_same_thread=False)
            print(f"Соединение с SQLite DB '{db_file}' установлено")
        except Error as e:
            print(f"Ошибка при подключении к базе данных SQLite: {e}")

    def set_data(self, sql_query, params=None):
        """Функция для записи чего-либо в бд"""

        # self.connection = sqlite3.connect(self.db_file)
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            self.connection.commit()
            print("Запрос выполнен успешно")
        except Error as e:
            print(f"Ошибка при выполнении запроса: {e}")

    def insert_data(self, table, params: dict):
        columns = str(tuple(params.keys())).replace("'", "")

        self.set_data(
            f"INSERT INTO {table} {columns} VALUES {str(tuple('?') * len(params.values())).replace("'", "")}",
            tuple(params.values())
        )

    def get_data(self, sql_query, params=None):
        """Функция для получения данных из БД"""
        # self.connection = sqlite3.connect(self.db_file)
        cursor = self.connection.cursor()
        result = None
        try:
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Ошибка при выполнении запроса на чтение: {e}")
            return result

    def update_data(self, table, updates, condition, params):
        """Обновление данных в таблице
            params - (1, 2, ...) кол-во условий в condition
            updates = {
                поле1: значение1,
                поле2: значение2,
                ...

            }
        """
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        full_params = list(updates.values()) + list(params)
        self.set_data(query, full_params)

    def close_connection(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            print("Соединение с SQLite DB закрыто")

    def add_user(self, params):

        self.insert_data(
            "users",
            params
        )

    def get_assessments(self, user_id):
        login, password = self.get_data(
            'SELECT login, password FROM users WHERE id = ?',
            (user_id,)
        )[0]

        if not (login and password):
            return 'Пользователь не автризован'

        # if os.path.exists(f'assessments_{login}_{password}.png'):
        #     return f'assessments_{login}_{password}.png'

        session = requests.Session()
        cookies_ = {}

        try:
            url = "https://kai.ru/main?p_p_id=58&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&_58_struts_action=%2Flogin%2Flogin"
            headers = {
                "cookie": "COOKIE_SUPPORT=true;"
            }
            data = {
                "_58_formDate": str(int(time.time())),
                "_58_saveLastPath": "false",
                "_58_redirect": "",
                "_58_doActionAfterLogin": "false",
                "_58_login": login,
                "_58_password": password
            }

            response = session.post(url, headers=headers, data=data, timeout=200)

            if response.status_code == 200:
                for cookie in session.cookies:
                    cookies_[cookie.name] = cookie.value
                headers = {
                    'Cookie': f"""JSESSIONID={cookies_['JSESSIONID']}"""
                }
                r = session.get(
                    'https://kai.ru/group/guest/student/attestacia',
                    headers=headers,
                    timeout=200
                )

                soup = BeautifulSoup(r.content, 'html.parser')

                table = soup.find_all('table')[2]

                table_html = str(table)

                html = f"""
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                table {{
                                    border-collapse: collapse;
                                    width: 100%;
                                }}
                                th, td {{
                                    border: 1px solid black;
                                    padding: 8px;
                                    text-align: left;
                                }}
                                th {{
                                    background-color: #f2f2f2;
                                }}
                            </style>
                        </head>
                        <body>
                            {table_html}
                        </body>
                        </html>
                        """

                self.update_data(
                    'education',
                    {
                        "assessments": html
                    }, "user_id = ?", (user_id, )
                )

                hti = Html2Image()

                hti.screenshot(html_str=html, save_as=f'assessments_{login}_{password}.png')

                return f'assessments_{login}_{password}.png'
        except Exception as e:
            print(e)
            return f'Неверный логин или пароль или нет данных об оценках'

    def get_schedule(self, user_id):
        login, password = self.get_data(
            'SELECT login, password FROM users WHERE id = ?',
            (user_id,)
        )[0]

        if not (login and password):
            return 'Пользователь не автризован'

        # if os.path.exists(f'assessments_{login}_{password}.png'):
        #     return f'assessments_{login}_{password}.png'

        session = requests.Session()
        cookies_ = {}

        try:
            url = "https://kai.ru/main?p_p_id=58&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&_58_struts_action=%2Flogin%2Flogin"
            headers = {
                "cookie": "COOKIE_SUPPORT=true;"
            }
            data = {
                "_58_formDate": str(int(time.time())),
                "_58_saveLastPath": "false",
                "_58_redirect": "",
                "_58_doActionAfterLogin": "false",
                "_58_login": login,
                "_58_password": password
            }

            response = session.post(url, headers=headers, data=data, timeout=200)

            if response.status_code == 200:
                for cookie in session.cookies:
                    cookies_[cookie.name] = cookie.value
                headers = {
                    'Cookie': f"""JSESSIONID={cookies_['JSESSIONID']}"""
                }
                r = session.get(
                    'https://kai.ru/group/guest/student/raspisanie',
                    headers=headers,
                    timeout=200
                )

                soup = BeautifulSoup(r.content, 'html.parser')

                table = soup.find_all('div', class_='control-group field-wrapper')[7]
                tables_images = []

                table_html = str(table)

                html = f"""
                                <html>
                                <head>
                                    <meta charset="utf-8">
                                    <style>
                                        table {{
                                            border-collapse: collapse;
                                            width: 100%;
                                        }}
                                        th, td {{
                                            border: 1px solid black;
                                            padding: 8px;
                                            text-align: left;
                                        }}
                                        th {{
                                            background-color: #f2f2f2;
                                        }}
                                    </style>
                                </head>
                                <body>
                                    {table_html}
                                </body>
                                </html>
                                """

                self.update_data(
                    'education',
                    {
                        "schedule": html
                    }, "user_id = ?", (user_id,)
                )

                hti = Html2Image()

                hti.browser.flags = ['--no-sandbox']
                # hti.browser.path = '/usr/bin/google-chrome'

                hti.screenshot(html_str=html, save_as=f'schedule_{login}_{password}.png')

                return f'schedule_{login}_{password}.png'
        except Exception as e:
            print(e)
            return f'Неверный логин или пароль или нет данных о расписании'

    def get_conferences(self, user_id):
        r = requests.get('https://na-konferencii.ru/')

        r = requests.post(
            'https://na-konferencii.ru/wp-admin/admin-ajax.php',
            data={
                "action": "filterhome",
                "nonce": extract_nonce(r.text),
                "page": "1",
            },
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "ru",
                "Cache-Control": "no-cache",
                "Content-Length": "216",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": "_ym_uid=171676082795127144; _ym_d=1716760827; _ym_isad=1; _ym_visorc=w",
                "Origin": "https://na-konferencii.ru",
                "Pragma": "no-cache",
                "Referer": "https://na-konferencii.ru/",
                "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"YaBrowser\";v=\"24.1\", \"Yowser\";v=\"2.5\"",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": "\"macOS\"",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

        )
        soup = BeautifulSoup(r.content, 'html.parser')
        messages = []

        for conference in soup.find_all('div', {'data': 'POST'}):
            conference_db = {}

            conference_db['theme'] = conference.find(class_='notice-item-title').find('a').get_text()
            conference_db['place'] = conference.find(class_='notice-item-top-location').find('p').get_text()
            dates = [i.strip() for i in conference.find(class_='notice-item-top-date').find('p').get_text().split('.')[0].split('-')]
            conference_db['start_time'] = dates[0]
            conference_db['finish_time'] = dates[1]
            conference_db['about'] = conference.find(class_='notice-item-body-inner').find_all('p')[0].get_text().strip()

            self.insert_data('conferences', conference_db)
            messages.append(
                f"<b>{conference_db['theme']}</b>\n\n🗺 {conference_db['place']}\n\n📅 {conference_db['start_time']} - {conference_db['finish_time']}\n\n📎 {conference_db['about']}"
            )

        return messages

    def get_olimpiads(self, user_id):
        r = requests.get(
            'https://olympiada.guppros.ru/'
        )

        soup = BeautifulSoup(r.content, 'html.parser')
        messages = []

        for olimpiad in soup.find_all('div', class_="student"):
            olimpiad_db = {}

            olimpiad_db['start_time'] = olimpiad.find('di', class_='feedback').get_text().strip()
            olimpiad_db['finish_time'] = ''

            olimpiad_db['subject'] = olimpiad.find(class_='contact').find('p', class_='tag').get_text().strip()
            olimpiad_db['conditions'] = olimpiad.find(class_='hover-option').find(class_='contact').find('p', class_='paragraph').get_text().strip()
            olimpiad_db['about'] = olimpiad.find(class_='hover-option').find(class_='contact').find(class_='title').get_text().strip()

            self.insert_data('olimpiads', olimpiad_db)
            messages.append(
                f"<b>{olimpiad_db['about']}</b>\n\n📚 {olimpiad_db['subject']}\n\n📅 {olimpiad_db['start_time']}\n\n📎 {olimpiad_db['conditions']}"
            )
        return messages

if __name__ == "__main__":
    db = DB("database.db")

    # db.add_user({
    #     "id": 2345,
    #     "login": "makarov.ru",
    #     "password": "123456",
    #     "first_name": "maxim",
    #     "last_name": "smirnov",
    #     "teacher_id": 123
    # })

    db.update_data('users', {
        "login": "MarakinDS999999",
        "password": "6ngz6vx39999999"
    }, "id = ?", (12345678, ))

    # print(db.get_assessments(12345678))

    # db.get_olimpiads(12345678)

    # логика при нажатии на Аттестация
    # status = db.get_assessments(user_id)
    # if status == '''Пользователь не автризован''':
    #     bot.send_message(user_id, '''Введите логин и пароль''')
    #     .... проверка логина пароль...
    #
    #     логин, пароль = из сообщения
    #
        # db.update_data('users', {
        #     "login": логин,
        #     "password": пароль
        # }, "id = ?", (user_id, ))
    #
    #     status = db.get_assessments(user_id) # это путь до файла, если все ок
    #     if status == ошибка:
    #         bot.send_message(user_id, '''логин и/или пароль не верны, введите еще раз (ты че дурак, твой пароль хуета, переделывай)''')
    #     else:
    #         bot.send_image(user_id, status)

    db.close_connection()
