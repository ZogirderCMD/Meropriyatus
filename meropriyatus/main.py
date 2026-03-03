import psycopg2, datetime, random, os
import nacl.encoding
import nacl.hash
from flask import Flask, request, render_template, make_response, url_for


con = psycopg2.connect(
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    database=os.getenv("POSTGRES_DB")
) # Подключение к базе данных

cur = con.cursor() # Перменная курсора базы данных

def query(q, a=()): # Функция для SQL запросов в базу данных
    try:
        cur.execute(q,a) # Выполнение SQL запроса
        con.commit() # Сохранение в базу данных
    except Exception as e:
        print(q, e)
        con.rollback() # Если будет ошибка, то совершится перевыполнение
        
def genUID(table):
    symbols = list("qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM")
    query(f"""SELECT uid FROM {table}""")
    restrIDs = tuple([i[0] for i in cur.fetchall()])
    while True:
        gotID = ''.join([random.choice(symbols) for i in range(8)])
        if gotID not in restrIDs: return gotID

def gen_session_key():
    symbols = list("qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM")
    query("""SELECT session_key FROM users""")
    restrIDs = tuple([i[0] for i in cur.fetchall()])
    while True:
        gotID = ''.join([random.choice(symbols) for i in range(25)])
        if gotID not in restrIDs: return gotID

def reformat_date(a:str,l:int=2):
    a=str(a)
    if len(a) < l: return "0"*(l-len(a))+a
    return a

query(open("tables.sql","r").read()) # Создание всех необходимых таблиц


class Calendar:
    uid:str = "0"*8
    name:str = ""
    owner:str = ""
    accessible:bool = False

    status:int = 100
    message:str = "Continue"
    
    def get(self, uid:str):
        query(f"""SELECT * FROM calendars WHERE uid = '{uid}'""")
        res = cur.fetchall()
        if res == []: return self.make_response(404, "Календарь не найден!")
        self.uid = res[0][0]
        self.name = res[0][1]
        self.owner = res[0][2]
        self.accessible = False
        return self.make_response(200, "Успешно!")
        
    def create(self, name:str=None, owner:int=None):
         
        if name is None: return self.make_response(403, "Имя календаря обязателено к заполнению!")
        if owner is None: return self.make_response(403, "Владелец календаря обязателен к заполнению!")
        if len(name)>30: return self.make_response(403, "Имя должно быть не более 30 символов!")
        self.uid = genUID("calendars")
        self.name = name
        self.owner = owner
        self.accessible = False
        query("""INSERT INTO calendars VALUES (%s, %s, %s)""", (self.uid, self.name, self.owner))
        return self.make_response(200, self.uid)
    def edit(self, name:str=None):
        if not name is None: self.name = name
        if not name is None and len(name)>30: return self.make_response(403, "Имя должно быть не более 30 символов!")
        self.save()
        return self.make_response(200, "Календарь успешно изменён!")
    def remove(self):
        query(f"""SELECT * FROM calendars WHERE uid='{self.uid}'""")
        res = cur.fetchall()
        if res == []: return self.make_response(403, "Календаря с таким uid не существует!")
        query(f"""DELETE FROM calendars WHERE uid='{self.uid}'""")
        return self.make_response(200, "Календарь успешно удалён!")
    
    def save(self):
        query("""UPDATE calendars SET name=%s WHERE uid=%s""", (self.name, self.uid))

    def make_response(self, a, b):
        self.status = a
        self.message = b
        return {"message":self.message}, self.status
    
    def jsonify(self):
        query(f"""SELECT uid FROM events WHERE calendar='{self.uid}'""")
        events = []
        for i in cur.fetchall():
            event = Event()
            event.get(i[0])
            events.append(event.jsonify())
        return {
            "uid": self.uid,
            "name": self.name,
            "events": events,
            "accessible": self.accessible
        }


class Event:
    uid:str = "0"*8
    name:str = ""
    desc:str = ""
    owner:str = ""
    calendar:str = ""
    date:datetime.datetime = datetime.datetime.now()

    status:int = 100
    message:str = "Continue"
    
    def get(self,uid:str):
        query(f"""SELECT * FROM events WHERE uid='{uid}'""")
        res = cur.fetchall()
        if res == []: return self.make_response(404, "Мероприятие не найдено!")
        self.uid = res[0][0]
        self.name = res[0][1]
        self.desc = res[0][2]
        self.owner = res[0][3]
        self.calendar = res[0][4]
        self.date = res[0][5]
        return self.make_response(200, "ОК")
    def create(self, name:str=None, desc:str="", owner:int=None, calendar:str=None, date:datetime.datetime=datetime.datetime.now()):
        if name is None: return self.make_response(403, "Имя мероприятия обязательно к заполнению!")
        if owner is None: return self.make_response(403, "Владелец мероприятия обязателен к заполнению!")
        if calendar is None: return self.make_response(403, "Календарь мероприятия обязательно к заполнению!")
        if len(name)>30: return self.make_response(403, "Имя должно быть не более 30 символов!")
        if len(desc)>300: return self.make_response(403, "Описание должно быть не более 300 символов!")
        self.uid = genUID("events")
        self.name = name
        self.desc = desc
        self.owner = owner
        self.calendar = calendar
        query("""INSERT INTO events VALUES (%s, %s, %s, %s, %s, %s)""", (self.uid, self.name, self.desc, self.owner, self.calendar, date))
        return self.make_response(200, "Мероприятие успешно создано!")
        
    def edit(self, name:str=None, desc:str=None, calendar:str=None, date:datetime.datetime=None):
        if not name is None: self.name = name
        if not date is None: self.date = date
        if not desc is None: self.desc = desc
        if not calendar is None: self.calendar = calendar
        if not name is None and len(name)>30: return self.make_response(403, "Имя должно быть не более 30 символов!")
        if not desc is None and len(desc)>300: return self.make_response(403, "Описание должно быть не более 300 символов!")
        self.save()
        return self.make_response(200, "Мероприятие успешно изменено!")

    def remove(self):
        query(f"""SELECT * FROM events WHERE uid='{self.uid}'""")
        res = cur.fetchall()
        if res == []: return self.make_response(404, "Мероприятие не найдено!")
        query(f"""DELETE FROM events WHERE uid='{self.uid}'""")
        return self.make_response(200, "Мероприятие удалено!")

    def save(self):
        query("""UPDATE events SET name=%s, "desc"=%s, calendar=%s, date=%s WHERE uid=%s""", (self.name, self.desc, self.calendar, self.date, self.uid))

    def make_response(self, a ,b):
        self.status = a
        self.message = b
        return {"message":self.message}, self.status

    def jsonify(self):

        fdate = f"{self.date.year}-{reformat_date(self.date.month)}-{reformat_date(self.date.day)}"

        return {
            "uid": self.uid,
            "name": self.name,
            "description": self.desc,
            "calendar": self.calendar,
            "date": fdate
        }


class User:
    uid:str = "0"*8
    login:str = ""
    password:str = ""
    session_key:str=""
    admin:bool = False
    events:list = []
    cals:list = []
    authed:bool = False

    status:int = 100
    message:str = "Continue"
    
    def register(self, login:str=None, password:str=None):
        query(f"""SELECT login FROM users WHERE login='{login}'""")
        res = cur.fetchall()
        if login == None: return self.make_response(403, "Введите логин!")
        if password == None: return self.make_response(403, "Введите пароль!")
        if res != []: return self.make_response(403, "Данный логин занят!")
        if len(login) > 30: return self.make_response(403, "Логин должен состоять максимум из 30 символов!")
        if len(login) < 6: return self.make_response(403, "Логин должен состоять минимум из 6 символов!")
        if len(password) < 6: return self.make_response(403, "Пароль должен состоять минимум из 6 символов!")
        encoded_pass = nacl.hash.sha512(password.encode("UTF-8"), encoder=nacl.encoding.HexEncoder).decode("UTF-8")
        self.uid = genUID("users")
        self.login = login
        self.password = encoded_pass
        self.session_key = gen_session_key()
        query(f"""INSERT INTO users VALUES ('{self.uid}', '{self.login}', '{self.password}', '{self.session_key}')""")
        return self.make_response(200, self.session_key)
    def enter(self, login:str=None, password:str=None):
        query(f"""SELECT pass,uid FROM users WHERE login='{login}'""")
        res = cur.fetchall()
        if login is None: return self.make_response(404, "Неправильный логин или пароль!")
        if password is None: return self.make_response(404, "Неправильный логин или пароль!")
        if res == []: return self.make_response(404, "Неправильный логин или пароль!")
        actual_pass = res[0][0]
        encoded_pass = nacl.hash.sha512(password.encode("UTF-8"), encoder=nacl.encoding.HexEncoder).decode("UTF-8")
        if actual_pass != encoded_pass: return self.make_response(404, "Неправильный логин или пароль!")
        self.uid = res[0][1]
        self.login = login
        self.password = encoded_pass
        self.session_key = gen_session_key()
        self.getElements()
        query("""UPDATE users SET session_key=%s WHERE uid=%s""", (self.session_key, self.uid))
        return self.make_response(200, self.session_key)
    def logout(self):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        self.session_key = gen_session_key()
        query("""UPDATE users SET session_key=%s WHERE uid=%s""", (self.session_key, self.uid))
        self.authed = False
        return self.make_response(200, "Успешно!")

    def auth(self, key:str=None):
        if key == None: return self.make_response(403, "Введите ключ сессии!")
        query(f"""SELECT * FROM users WHERE session_key='{key}'""")
        res = cur.fetchall()
        if res == []: return self.make_response(404, "Неизвестый ключ сессии!")
        self.uid = res[0][0]
        self.login = res[0][1]
        self.password = res[0][2]
        self.authed = True
        self.getElements()
        return self.make_response(200, "Успешный вход в систему!")
    def remove(self):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        query(f"""DELETE FROM events WHERE owner='{self.uid}'""")
        query(f"""DELETE FROM calendars WHERE owner='{self.uid}'""")
        query(f"""DELETE FROM users WHERE login='{self.login}'""")
        self.authed = False
        return self.make_response(200, "Аккаунт удалён!")
    def createEvent(self, name:str, desc:str, calendar:str, date:datetime.datetime=datetime.datetime.now()):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        status = Event().create(name, desc, self.uid, calendar, date)
        self.getElements()
        return status
    def getEvent(self, uid:str):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.events: return self.make_response(404, "Мероприятие не найдено!")
        event = Event()
        result = event.get(uid)
        if result[1] != 200: return result
        return event.jsonify()
    def editEvent(self, uid:str=None, name:str=None, desc:str=None, calendar:str=None, date:datetime.datetime=None):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.events: return self.make_response(404, "Мероприятие не найдено!")
        event = Event()
        result = event.get(uid)
        if result[1] != 200: return result
        status = event.edit(name, desc, calendar, date)
        return status
    def deleteEvent(self, uid:str):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.events: return self.make_response(404, "Мероприятие не найдено!")
        event = Event()
        result = event.get(uid)
        if result[1] != 200: return result
        status = event.remove()
        self.getElements()
        return status
    def createCalendar(self, name:str):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        status = Calendar().create(name, self.uid)
        self.getElements()
        return status
    def getCalendar(self, uid:str):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.cals: return self.make_response(404, "Календарь не найден!")
        cal = Calendar()
        result = cal.get(uid)
        if result[1] != 200: return result
        return cal.jsonify()
    def editCalendar(self, uid:str=None, name:str=None):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.cals: return self.make_response(404, "Календарь не найден!")
        cal = Calendar()
        result = cal.get(uid)
        if result[1] != 200: return result
        status = cal.edit(name)
        return status
    def deleteCalendar(self, uid:str):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        if not uid in self.cals: return self.make_response(404, "Календарь не найден!")
        cal = Calendar()
        result = cal.get(uid)
        if result[1] != 200: return result
        status = cal.remove()
        self.getElements()
        return status
    
    def getElements(self):
        if self.authed is False: return self.make_response(403, "Сначала зайдите в аккаунт!")
        query(f"""SELECT uid FROM events WHERE owner='{self.uid}'""")
        self.events = [i[0] for i in cur.fetchall()]
        query(f"""SELECT uid FROM calendars WHERE owner='{self.uid}'""")
        self.cals = [i[0] for i in cur.fetchall()]

    def make_response(self, a, b):
        self.status = a
        self.message = b
        return {"message":self.message}, self.status
    
    def jsonify(self):
        calendars = []
        events = []
        for i in self.cals:
            calendar = Calendar()
            calendar.get(i)
            calendars.append(calendar.jsonify())
        for i in self.events:
            event = Event()
            event.get(i)
            events.append(event.jsonify())
        return {
            "uid": self.uid,
            "username": self.login,
            "calendars": calendars,
            "events": events
        }

app = Flask(__name__) # Инициализация приложения Flask

@app.route("/api/user/register", methods=["POST"])
def user_register():
    user = User()
    login = request.form.get('login', None)
    passw = request.form.get('pass', None)
    result = user.register(login, passw)
    if result[1] != 200: return result
    resp = make_response(result)
    resp.set_cookie(
        "key",
        user.session_key
    )
    return resp

@app.route("/api/user/login", methods=["POST"])
def user_login():
    user = User()
    login = request.form.get('login', None)
    passw = request.form.get('pass', None)
    result = user.enter(login, passw)
    if result[1] != 200: return result
    resp = make_response(result)
    key = request.cookies.get('key', None)
    if not key is None:
        resp.set_cookie(
            "key",
            user.session_key
        )
    return resp

@app.route("/api/user", methods=["GET", "DELETE", "POST"])
def user_account():
    user = User()
    key = request.cookies.get('key', None)
    result = user.auth(key)
    if result[1] != 200: return result
    if request.method == "DELETE":
        return user.remove()
    if request.method == "GET":
        return user.jsonify()
    if request.method == "POST":
        return user.logout()

@app.route("/api/user/calendar", methods=["GET", "POST", "PATCH", "DELETE"])
def user_calendar():
    user = User()
    key = request.cookies.get('key', None)
    result = user.auth(key)
    uid = request.form.get('uid', '0')
    if result[1] != 200: return result
    if request.method == "GET":
        return user.getCalendar(uid)
    if request.method == "POST":
        name = request.form.get('name', None)
        return user.createCalendar(name)
    if request.method == "PATCH":
        name = request.form.get('name', None)
        return user.editCalendar(uid, name)
    if request.method == "DELETE":
        return user.deleteCalendar(uid)

@app.route("/api/user/event", methods=["GET", "POST", "PATCH", "DELETE"])
def user_event():
    user = User()
    key = request.cookies.get('key', None)
    result = user.auth(key)
    uid = request.form.get('uid', '0')
    if result[1] != 200: return result
    if request.method == "GET":
        return user.getEvent(uid)
    if request.method == "POST":
        name = request.form.get('name', None)
        desc = request.form.get('desc', None)
        calendar = request.form.get('calendar', None)
        date_raw = request.form.get('date', None).split("-")
        try: date = datetime.datetime(int(date_raw[0]),int(date_raw[1]),int(date_raw[2]))
        except IndexError: return {"message": "Правильный формат даты - ГГГГ-ММ-ДД"}, 403
        except ValueError: return {"message": "Год, месяц, день должны быть числами!"}, 403
        try: return user.createEvent(name, desc, calendar, date)
        except: return user.createEvent(name, desc, calendar, date=date)
    if request.method == "PATCH":
        name = request.form.get('name', None)
        desc = request.form.get('desc', None)
        calendar = request.form.get('calendar', None)
        date_raw = request.form.get('date', None).split("-")
        try:
            date = datetime.datetime(int(date_raw[0]),int(date_raw[1]),int(date_raw[2]))
        except IndexError: return {"message": "Правильный формат даты - ГГГГ-ММ-ДД"}, 403
        except ValueError: return {"message": "Год, месяц, день должны быть числами!"}, 403
        return user.editEvent(uid, name, desc, calendar, date)
    if request.method == "DELETE":
        return user.deleteEvent(uid)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/calendars")
def calendars():
    return render_template("calendars.html")

@app.route("/events")
def events():
    return render_template("events.html")

