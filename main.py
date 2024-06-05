import telebot
from telebot import types
import requests
from lxml import html
from data_base import DB
from pprint import pprint
import sqlite3

db = DB('database.db')
bot = telebot.TeleBot("6727981805:AAEY_QGB9K4ASzkbT2Q742oMyY3ElEJYLuE")

def parse_documents():
    url = "https://abiturientu.kai.ru/bakalavriat"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        element = tree.xpath('/html/body/div[2]/div[1]/div[2]/div/div/div/div/section/div/div/div/div[1]/div/div[1]/div/div/div/div[2]/p[1]')
        if element:
            text_content = [text.strip() for text in element[0].xpath('.//text()') if text.strip()]
            text_content.pop(0)
            return '\n'.join(text_content)
        else:
            return "Список документов не найден."
    else:
        return "Ошибка при запросе к веб-странице."

def parse_document_link():
    url = "https://abiturientu.kai.ru/bakalavriat"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        element = tree.xpath('/html/body/div[2]/div[1]/div[2]/div/div/div/div/section/div/div/div/div[1]/div/div[1]/div/div/div/div[2]/div/div/span/a')
        if element:
            link = element[0].get('href')
            return link
        else:
            return "Ссылка на документ не найдена."
    else:
        return "Ошибка при запросе к веб-странице."


def abiturient_kontact():
    url = "https://abiturientu.kai.ru/kontakty"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        elements = tree.xpath(
            '/html/body/div[2]/div[1]/div[2]/div/div/div/div/section/div/div/div/div[1]/div/p[position() = 3 or position() = 4 or position() = 5 or position() = 6 or position() = 7]')
        kontakt = ["Телефоны:\n"]
        for element in elements:
            text = element.text_content().strip()
            if text:
                if elements.index(element) == 0:
                    telefon_text = text.replace("Телефоны:", "").strip()
                    kontakt.append(f"{telefon_text}\n")
                elif elements.index(element) == 4:
                    social_text = text.replace("Соцсети:", "").strip()
                    kontakt.append(f"{social_text}\n")
                else:
                    kontakt.append(f"{text}\n")
        return kontakt
    else:
        return []


def abiturient_adress():
    url = "https://abiturientu.kai.ru/kontakty"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        elements = tree.xpath(
            '/html/body/div[2]/div[1]/div[2]/div/div/div/div/section/div/div/div/div[1]/div/p[3]')
        adress = [element.text_content().replace('Телефоны:', ' ').strip() for element in elements]
        formatted_text = "<b>Телефоны:</b>\n\n"
        if adress:
            for i, text in enumerate(adress):
                if i == 0:
                    formatted_text += f"{text}\n\n"
                else:
                    formatted_text += f"{text}\n"
        table_rows = tree.xpath(
            '/html/body/div[2]/div[1]/div[2]/div/div/div/div/section/div/div/div/div[1]/div/div[1]/table/tbody/tr')
        table_text = "<b>Режим работы приёмной комиссии:</b>\n\n"
        for row in table_rows:
            day_elements = row.xpath('./td[1]/text()')
            time_elements = row.xpath('./td[2]/text()')
            if day_elements:
                day = day_elements[0].strip()
                if "суббота" in day.lower() or "воскресенье" in day.lower():
                    table_text += f"{day}: выходной\n"
                elif time_elements:
                    time = time_elements[0].strip()
                    table_text += f"{day}: {time}\n"
                else:
                    table_text += f"{day}: с 9:00 до 17:00\n"
        return formatted_text + table_text
    else:
        return "Ошибка при запросе к веб-странице."


def get_specialties_text():
    url = "https://abiturientu.kai.ru/bakalavriat"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        tree = html.fromstring(html_content)
        elements = tree.xpath('//table/tbody/tr/td[2]')
        specialties = [element.text_content().strip() for element in elements]
        return specialties
    else:
        return []


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('Студент', 'Абитуриент')

    db.add_user({
        'id': message.chat.id,
        'first_name': message.chat.first_name,
        'last_name': message.chat.last_name
    })
    bot.send_message(message.chat.id, "Привет! Выберите вашу роль:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Студент', 'Абитуриент'])
def menu(message):
    if message.text == 'Студент':
        student_menu(message)
    elif message.text == 'Абитуриент':
        abiturient_menu(message)


def student_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Рассчитать стипендию', 'Узнать расписание', 'Аттестация', 'Четная/нечетная неделя', 'Конференции',
               'Олимпиады', 'Назад')
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_student_options)


def handle_student_options(message):
    if message.text == 'Рассчитать стипендию':
        start_scholarship_calculation(message)
    elif message.text == 'Четная/нечетная неделя':
        bot.send_message(message.chat.id, 'Нечетная неделя', reply_markup=add_back_button2())
    elif message.text == 'Назад':
        send_welcome(message)
    elif message.text == 'Конференции':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Назад')
        for conference in db.get_conferences(message.chat.id)[:5]:
            bot.send_message(message.chat.id, conference, parse_mode='HTML', reply_markup=markup)
        bot.register_next_step_handler(message, handle_student_menu)
    elif message.text == 'Олимпиады':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Назад')
        for olimpiad in db.get_olimpiads(message.chat.id)[:5]:
            bot.send_message(message.chat.id, olimpiad, parse_mode='HTML', reply_markup=markup)
        bot.register_next_step_handler(message, handle_student_menu)
    elif message.text == 'Аттестация':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Назад')

        status = db.get_assessments(message.chat.id)
        pprint(status)
        if status == 'Пользователь не автризован':
            bot.send_message(message.chat.id, 'Вы не авторизованы, введите логин и пароль от сайта КАИ через запятую и пробел')
            bot.register_next_step_handler(message, handle_student_auth_assessments)
        elif status == 'Неверный логин или пароль или нет данных об оценках':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Назад', 'Изменить логин и пароль')
            bot.send_message(message.chat.id, status, parse_mode='HTML',  reply_markup=markup)
            bot.register_next_step_handler(message, handle_student_menu)
        else:
            bot.send_photo(message.chat.id, open(status, 'rb'))
            student_menu(message)
    elif message.text == 'Узнать расписание':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Назад')

        status = db.get_schedule(message.chat.id)
        if status == 'Пользователь не автризован':
            bot.send_message(message.chat.id, 'Вы не авторизованы, введите логин и пароль от сайта КАИ через запятую и пробел')
            bot.register_next_step_handler(message, handle_student_auth_schedule)
        elif status == 'Неверный логин или пароль или нет данных о расписании':
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Назад', 'Изменить логин и пароль')
            bot.send_message(message.chat.id, status, parse_mode='HTML',  reply_markup=markup)
            bot.register_next_step_handler(message, handle_student_menu)
        else:
            bot.send_photo(message.chat.id, open(status, 'rb'))
            student_menu(message)



def handle_student_menu(message):
    if message.text == 'Назад':
        student_menu(message)
    elif message.text == 'Изменить логин и пароль':
        bot.send_message(message.chat.id,
                         'Введите логин и пароль от сайта КАИ через запятую и пробел')
        bot.register_next_step_handler(message, handle_student_auth)


def handle_student_auth_assessments(message):
    if len(message.text.split(', ')) != 2:
        bot.send_message(message.chat.id, 'В строке нет логина и пароля, они должны быть через запятую и пробел')
        bot.register_next_step_handler(message, handle_student_auth_assessments)
    else:
        login, password = message.text.split(', ')
        db.update_data('users', {
            "login": login,
            "password": password
        }, "id = ?", (message.chat.id, ))

        message.text = 'Аттестация'
        handle_student_options(message)

def handle_student_auth_schedule(message):
    if len(message.text.split(', ')) != 2:
        bot.send_message(message.chat.id, 'В строке нет логина и пароля, они должны быть через запятую и пробел')
        bot.register_next_step_handler(message, handle_student_auth_schedule)
    else:
        login, password = message.text.split(', ')
        db.update_data('users', {
            "login": login,
            "password": password
        }, "id = ?", (message.chat.id, ))

        message.text = 'Узнать расписание'
        handle_student_options(message)


def abiturient_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Адрес и график работы приемной комиссии", "Место в рейтинге на поступление",
               "Список документов, необходимых для поступления", "Информация об общежитиях ВУЗа",
               "Контактные данные приемной комиссии", "Как проходит отбор в военно-учебный центр", "Назад")
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_abiturient_options)

def handle_abiturient_options(message):
    if message.text == "Список документов, необходимых для поступления":
        documents_list = parse_documents()
        bot.send_message(message.chat.id, f"<b>Список документов:</b>\n\n {documents_list}", parse_mode='HTML')
        document_link = parse_document_link()
        bot.send_message(message.chat.id, f"<b>Доверенность (образец):</b>\n\n {document_link}", parse_mode='HTML', reply_markup=add_back_button())
    elif message.text == "Место в рейтинге на поступление":
        bot.send_message(message.chat.id,
                         " <b>Ссылка для просмотра рейтинга</b>\n\n"
                         '<i>https://abiturientu.kai.ru/dokumenty-postupivsie-online</i>',
                         parse_mode='HTML', reply_markup=add_back_button())

    elif message.text == "Специальности ВУЗа":
        send_specialties_menu(message.chat.id)
    elif message.text == "Контактные данные приемной комиссии":
        kontakt_info = abiturient_kontact()
        if kontakt_info:
            response_message = "\n".join(kontakt_info)
        else:
            response_message = "Не удалось получить контактную информацию."
        bot.send_message(message.chat.id, response_message, parse_mode='HTML', reply_markup=add_back_button())
    elif message.text == "Адрес и график работы приемной комиссии":
        adress_info = abiturient_adress()
        if adress_info:
            bot.send_message(message.chat.id, adress_info, parse_mode='HTML', reply_markup=add_back_button())

    elif message.text == "Как проходит отбор в военно-учебный центр":
        bot.send_message(message.chat.id,
                        " <b>Как проходит отбор в военный учебный центр</b>\n\n"
                        " - Отбор для обучения в Военный учебный центр происходит в два этапа.\n"
                        " - Предварительный отбор проводится по направлению начальника ВУЦ военными комиссариатами, в которых студенты состоят на воинском учёте, и включает в себя прохождение военно-врачебной комиссии и профессионально-психологического отбора или по-другому ППО.\n"
                        " - Результатом прохождения комиссии должно быть заключение «годен к военной службе» или «годен к военной службе с незначительными ограничениями».\n"
                        " - В результате прохождения ППО студент должен получить первую или вторую группу. Граждане, получившие третью группу профессионально-психологического отбора, допускаются к основному отбору во вторую очередь.\n"
                        " - Документы о прохождении предварительного отбора студент представляет в военный учебный центр в установленные сроки.\n"
                        " - Студенты, не прошедшие предварительный отбор или не представившие документы в установленные сроки, к основному отбору не допускаются.\n"
                        " - При проведении основного отбора анализируется уровень успеваемости студента по итогам всех семестров, предшествующих началу основного отбора, а также уровень его физической подготовки.\n"
                        " - В результате составляется рейтинговый список студентов, из которого отбирается необходимое количество учащихся в соответствии с заказом на подготовку офицеров, сержантов и солдат по конкретной военно-учётной специальности.",
                         parse_mode='HTML', reply_markup=add_back_button()
        )
    elif message.text == "Информация об общежитиях ВУЗа":
        bot.send_message(message.chat.id,
                         "1) Общежитие №1/ ул. Б. Красная, 7/9\n"
                         "2) Общежитие №2/ ул. Б. Красная, 18\n"
                         "3) Общежитие №3/ ул. Ак. Кирпичникова, 11\n"
                         "4) Общежитие №4/ ул. Короленко, 85\n"
                         "5) Общежитие №5/ ул. Н. Ершова 30\n"
                         "6) Общежитие №6/ ул. Товарищеская, 30\n"
                         "7) Общежитие №7/ ул. Товарищеская, 30 «а»", reply_markup=add_back_button())
    elif message.text == "Назад":
        send_welcome(message)


def add_back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button = types.KeyboardButton("Назад")
    markup.add(back_button)
    return markup

@bot.message_handler(func=lambda message: message.text == "Назад")
def handle_back_button(message):
    abiturient_menu(message)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def handle_back_button(call):
    abiturient_menu(call.message)
    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data == "back")
def callback_back(call):
    message_id = call.message.message_id
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, message_id)
    previous_message = call.message.reply_to_message
    if previous_message:
        bot.delete_message(chat_id, previous_message.message_id)
    send_welcome(types.Message(message_id=None, from_user=None, date=None, chat=types.Chat(id=chat_id, type='private'),
                               content_type='text', options={}, json_string={}))


def start_scholarship_calculation(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Бакалавр', 'Специалитет', 'Магистр', 'Назад')
    msg = bot.send_message(message.chat.id, "Выберите вашу ступень обучения:", reply_markup=markup)
    bot.register_next_step_handler(msg, get_degree)


def get_degree(message):
    text = message.text
    chat_id = message.chat.id

    if text in ['Бакалавр', 'Специалитет']:
        msg = bot.send_message(chat_id, "На каком семестре вы обучаетесь?", reply_markup=add_back_button())
        bot.register_next_step_handler(msg, bachelor_specialist, text)
    elif text == 'Магистр':
        msg = bot.send_message(chat_id, "На каком семестре вы обучаетесь?", reply_markup=add_back_button())
        bot.register_next_step_handler(msg, master, text)
    elif text == 'Назад':
        student_menu(message)
    else:
        bot.send_message(chat_id, "Пожалуйста, выберите корректную ступень обучения.")
        start_scholarship_calculation(message)

def add_back_button2():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button = types.KeyboardButton("Hазад")
    markup.add(back_button)
    return markup

@bot.message_handler(func=lambda message: message.text == "Hазад")
def handle_back_button(message):
    student_menu(message)


def bachelor_specialist(message, degree):
    try:
        if message.text == 'Назад':
            student_menu(message)
            return

        semester = int(message.text)
        chat_id = message.chat.id

        if semester == 1:
            msg = bot.send_message(chat_id, "Сколько баллов за вступительные испытания вы получили?",
                                   reply_markup=add_back_button2())
            bot.register_next_step_handler(msg, first_semester_score)
        else:
            msg = bot.send_message(chat_id, "Получаете ли вы стипендию ученого совета Университета? (Да/Нет)",
                                   reply_markup=yes_no_back_keyboard())
            bot.register_next_step_handler(msg, other_semesters, degree)
    except ValueError:
        bot.send_message(message.chat.id, "Введите числовое значение семестра.", reply_markup=add_back_button2())
        bot.register_next_step_handler(message, bachelor_specialist, degree)


def first_semester_score(message):
    try:
        if message.text == 'Назад':
            student_menu(message)
            return

        score = int(message.text)
        chat_id = message.chat.id

        if score >= 260:
            bot.send_message(chat_id, 'Размер вашей стипендии 12000 рублей', reply_markup=add_back_button2())
        elif score >= 240:
            bot.send_message(chat_id, 'Размер вашей стипендии 10400 рублей', reply_markup=add_back_button2())
        elif score >= 220:
            bot.send_message(chat_id, 'Размер вашей стипендии 7800 рублей', reply_markup=add_back_button2())
        elif score >= 200:
            bot.send_message(chat_id, 'Размер вашей стипендии 5200 рублей', reply_markup=add_back_button2())
        else:
            bot.send_message(chat_id, 'Размер вашей стипендии 2600 рублей', reply_markup=add_back_button2())
    except ValueError:
        bot.send_message(message.chat.id, "Введите числовое значение баллов.", reply_markup=add_back_button2())
        bot.register_next_step_handler(message, first_semester_score)


def other_semesters(message, degree):
    if message.text == 'Назад':
        student_menu(message)
        return
    response = message.text
    chat_id = message.chat.id
    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 4400 рублей', reply_markup=add_back_button2())
    else:
        msg = bot.send_message(chat_id, "Получаете ли вы стипендию Ученого совета Института? (Да/Нет)",
                               reply_markup=yes_no_back_keyboard())
        bot.register_next_step_handler(msg, institute_council_scholarship, degree)


def institute_council_scholarship(message, degree):
    if message.text == 'Назад':
        student_menu(message)
        return
    response = message.text
    chat_id = message.chat.id
    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 3850 рублей', reply_markup=add_back_button2())
    else:
        msg = bot.send_message(chat_id, "Есть ли у вас долги или оценки удовлетворительно за прошлый семестр? (Да/Нет)",
                               reply_markup=yes_no_back_keyboard())
        bot.register_next_step_handler(msg, debts_or_passing_grades, degree)


def debts_or_passing_grades(message, degree):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        msg = bot.send_message(chat_id, "Получаете ли вы социальную стипендию? (Да/Нет)",
                               reply_markup=yes_no_back_keyboard())
        bot.register_next_step_handler(msg, social_scholarship)
    else:
        msg = bot.send_message(chat_id,
                               "На какие оценки вы сдали экзамены, курсовые работы, практики? (На хорошо/На хорошо и отлично/На отлично)",
                               reply_markup=add_back_button2())
        bot.register_next_step_handler(msg, grades_evaluation)


def social_scholarship(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 3300 рублей', reply_markup=add_back_button2())
    else:
        bot.send_message(chat_id, 'К сожалению, у вас нет стипендии', reply_markup=add_back_button2())


def grades_evaluation(message):
    if message.text == 'Назад':
        student_menu(message)
        return
    response = message.text
    chat_id = message.chat.id
    if response == 'На хорошо':
        bot.send_message(chat_id, 'Размер вашей стипендии 2200 рублей + социальная стипендия', reply_markup=add_back_button2())
    elif response == 'На хорошо и отлично':
        bot.send_message(chat_id, 'Размер вашей стипендии 2750 рублей + социальная стипендия', reply_markup=add_back_button2())
    elif response == 'На отлично':
        bot.send_message(chat_id, 'Размер вашей стипендии 3300 рублей + социальная стипендия', reply_markup=add_back_button2())


def master(message, degree):
    try:
        if message.text == 'Назад':
            student_menu(message)
            return

        semester = int(message.text)
        chat_id = message.chat.id

        if semester == 1:
            bot.send_message(chat_id, 'Размер вашей стипендии 3300 рублей')
        else:
            msg = bot.send_message(chat_id, "Получаете ли вы стипендию ученого совета Университета? (Да/Нет)",
                                   reply_markup=yes_no_back_keyboard())
            bot.register_next_step_handler(msg, master_scholarship)
    except ValueError:
        bot.send_message(message.chat.id, "Введите числовое значение семестра.", reply_markup=add_back_button2())
        bot.register_next_step_handler(message, master, degree)


def master_scholarship(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 6600 рублей', reply_markup=add_back_button2())
    else:
        msg = bot.send_message(chat_id, "Получаете ли вы стипендию Ученого совета Института? (Да/Нет)",
                               reply_markup=yes_no_back_keyboard())
        bot.register_next_step_handler(msg, master_institute_council_scholarship)


def master_institute_council_scholarship(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 5775 рублей', reply_markup=add_back_button2())
    else:
        msg = bot.send_message(chat_id, "Есть ли у вас долги или оценки удовлетворительно за прошлый семестр? (Да/Нет)",
                               reply_markup=yes_no_back_keyboard())
        bot.register_next_step_handler(msg, master_debts_or_passing_grades)


def master_debts_or_passing_grades(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        msg = bot.send_message(chat_id, "Получаете ли вы социальную стипендию? (Да/Нет)")
        bot.register_next_step_handler(msg, master_social_scholarship)
        reply_markup = yes_no_back_keyboard()
    else:
        msg = bot.send_message(chat_id,
                               "На какие оценки вы сдали экзамены, курсовые работы, практики? (На хорошо/На хорошо и отлично/На отлично)",
                               reply_markup=add_back_button2())
        bot.register_next_step_handler(msg, master_grades_evaluation)


def master_social_scholarship(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response.lower() == 'да':
        bot.send_message(chat_id, 'Размер вашей стипендии 4950 рублей', reply_markup=add_back_button2())
    else:
        bot.send_message(chat_id, 'К сожалению, у вас нет стипендии', reply_markup=add_back_button2())


def master_grades_evaluation(message):
    if message.text == 'Назад':
        student_menu(message)
        return

    response = message.text
    chat_id = message.chat.id

    if response == 'На хорошо':
        bot.send_message(chat_id, 'Размер вашей стипендии 3300 рублей + социальная стипендия', reply_markup=add_back_button2())
    elif response == 'На хорошо и отлично':
        bot.send_message(chat_id, 'Размер вашей стипендии 4125 рублей + социальная стипендия', reply_markup=add_back_button2())
    elif response == 'На отлично':
        bot.send_message(chat_id, 'Размер вашей стипендии 4950 рублей + социальная стипендия', reply_markup=add_back_button2())


def yes_no_back_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    keyboard.add('Да', 'Нет')
    return keyboard


bot.polling()
