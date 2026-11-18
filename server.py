from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import random
import sqlite3

app = FastAPI()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE, name TEXT, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '', lang TEXT DEFAULT 'ru')''')
    conn.commit()
    conn.close()

init_db()

# --- МОДЕЛИ ДАННЫХ ---
class RegRequest(BaseModel):
    email: str
    name: str
    lang: str

class AdminAction(BaseModel):
    admin_pass: str
    target_email: str
    action: str
    value: str

# --- HTML САЙТ ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram</title>
    <style>
        body { background-color: #0e1621; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background-color: #17212b; padding: 30px; border-radius: 15px; text-align: center; width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #64b5f6; margin-bottom: 20px; }
        input, select { width: 90%; padding: 12px; margin: 8px 0; border-radius: 8px; border: none; background-color: #242f3d; color: white; outline: none; }
        button { background-color: #64b5f6; color: #0e1621; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 15px; transition: 0.3s; }
        button:hover { background-color: #42a5f5; }
        .google-btn { background-color: white; color: #333; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 15px; }
        .google-btn:hover { background-color: #eee; }
        .hidden { display: none; }
        .admin-panel { border-top: 1px solid #333; margin-top: 20px; padding-top: 20px; text-align: left; }
        .badge { background: red; padding: 2px 5px; border-radius: 5px; font-size: 10px; margin-left: 5px; }
        .nav { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .nav button { width: auto; padding: 5px 10px; margin: 0; background: #242f3d; color: white; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <button onclick="showLang('ru')">RU</button>
        <button onclick="showLang('uk')">UA</button>
        <button onclick="showLang('en')">EN</button>
    </div>
    
    <h1 id="title">NFTgram</h1>

    <!-- ЭКРАН ВХОДА -->
    <div id="loginScreen">
        <p id="loginText">Войдите в свой аккаунт</p>
        <!-- КНОПКА GOOGLE -->
        <button class="google-btn" onclick="googleLogin()">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="20"> 
            Войти через Google
        </button>
        <hr style="border-color: #333; margin: 20px 0;">
        <p style="font-size: 12px; color: gray;">Или введите почту вручную (если у вас уже есть аккаунт)</p>
        <input type="email" id="loginEmail" placeholder="Почта">
        <input type="password" id="loginPass" placeholder="Пароль">
        <button onclick="login()">Войти по паролю</button>
    </div>

    <!-- ПРОФИЛЬ -->
    <div id="profileScreen" class="hidden">
        <h2 id="profName">Имя</h2>
        <p id="profPhone" style="color: #64b5f6; font-size: 20px;">+0000</p>
        <p id="profPass" style="font-size: 12px; color: gray;">Пароль: ****</p>
        <p id="profStatus"></p>
        
        <div style="text-align: left; margin-top: 20px;">
            <label>Сменить имя:</label>
            <input type="text" id="newName">
            <label>Сменить номер:</label>
            <input type="text" id="newPhone">
            <button onclick="updateProfile()">Сохранить</button>
        </div>

        <!-- АДМИН ПАНЕЛЬ -->
        <div class="admin-panel" id="adminPanel">
            <h3>Админ-панель</h3>
            <input type="text" id="adminTarget" placeholder="Почта пользователя">
            <select id="adminAction">
                <option value="badge">Выдать отметку</option>
                <option value="stars">Дать звезды</option>
                <option value="status">Сделать админом</option>
            </select>
            <input type="text" id="adminValue" placeholder="Значение (SCAM, 9999, admin)">
            <button onclick="adminAction()">Выполнить</button>
        </div>
    </div>
</div>

<script>
    let currentUser = null;

    function showLang(lang) {
        const texts = {
            ru: { title: "NFTgram", login: "Войдите в свой аккаунт" },
            uk: { title: "NFTgram", login: "Увійдіть у свій акаунт" },
            en: { title: "NFTgram", login: "Log in to your account" }
        };
        document.getElementById('title').innerText = texts[lang].title;
        document.getElementById('loginText').innerText = texts[lang].login;
    }

    function showScreen(id) {
        document.getElementById('loginScreen').classList.add('hidden');
        document.getElementById('profileScreen').classList.add('hidden');
        document.getElementById(id).classList.remove('hidden');
    }

    // ИМИТАЦИЯ ВХОДА ЧЕРЕЗ GOOGLE
    async function googleLogin() {
        const email = prompt("Введите вашу почту Google (Gmail):");
        if (!email) return;

        // Отправляем на сервер запрос "Войти или создать"
        const res = await fetch('/api/google_login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email})
        });
        
        if (res.ok) {
            currentUser = await res.json();
            showProfile();
        } else {
            alert("Ошибка входа");
        }
    }

    async function login() {
        const email = document.getElementById('loginEmail').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, password: pass})
        });
        if (res.ok) {
            currentUser = await res.json();
            showProfile();
        } else {
            alert("Неверная почта или пароль!");
        }
    }

    function showProfile() {
        showScreen('profileScreen');
        document.getElementById('profName').innerText = currentUser.name;
        document.getElementById('profPhone').innerText = currentUser.phone;
        document.getElementById('profPass').innerText = "Пароль: " + currentUser.password;
        
        let badgeHtml = currentUser.badge ? `<span class="badge">${currentUser.badge}</span>` : '';
        document.getElementById('profStatus').innerHTML = `Статус: ${currentUser.status} ${badgeHtml}`;

        if (currentUser.status === 'admin' || currentUser.password === 'Davolek') {
            document.getElementById('adminPanel').style.display = 'block';
        } else {
            document.getElementById('adminPanel').style.display = 'none';
        }
    }

    async function updateProfile() {
        const newName = document.getElementById('newName').value;
        const newPhone = document.getElementById('newPhone').value;
        if (!newName && !newPhone) return;

        const res = await fetch('/api/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: currentUser.email, new_name: newName, new_phone: newPhone})
        });
        alert("Профиль обновлен! Перезайдите.");
        location.reload();
    }

    async function adminAction() {
        const target = document.getElementById('adminTarget').value;
        const action = document.getElementById('adminAction').value;
        const value = document.getElementById('adminValue').value;
        
        if (currentUser.password !== 'Davolek' && currentUser.status !== 'admin') return alert("Нет прав!");

        const res = await fetch('/api/admin_action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: currentUser.password, target_email: target, action: action, value: value})
        });
        if (res.ok) {
            alert("Действие выполнено!");
        } else {
            alert("Ошибка прав админа!");
        }
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_PAGE

# --- API ---
@app.post("/api/google_login")
def google_login(data: dict):
    email = data.get("email")
    if not email: raise HTTPException(status_code=400, detail="Email обязателен")
    
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    
    # Ищем пользователя
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    
    if not user:
        # Если нет — регистрируем
        phone = f"+8{random.randint(100000000, 999999999)}"
        password = str(random.randint(100000, 999999))
        name = email.split('@')[0] # Имя из почты
        c.execute("INSERT INTO users (email, name, phone, password) VALUES (?, ?, ?, ?)",
                  (email, name, phone, password))
        conn.commit()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
    
    conn.close()
    return {"email": user[1], "name": user[2], "phone": user[3], "password": user[4], "status": user[6], "badge": user[7]}

@app.post("/api/login")
def login_user(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data.get("email"), data.get("password")))
    user = c.fetchone()
    conn.close()
    if user:
        return {"email": user[1], "name": user[2], "phone": user[3], "password": user[4], "status": user[6], "badge": user[7]}
    raise HTTPException(status_code=401, detail="Неверный пароль")

@app.post("/api/update_profile")
def update_profile(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("new_name"):
        c.execute("UPDATE users SET name = ? WHERE email = ?", (data.get("new_name"), data.get("email")))
    if data.get("new_phone"):
        c.execute("UPDATE users SET phone = ? WHERE email = ?", (data.get("new_phone"), data.get("email")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin_action")
def admin_action(data: AdminAction):
    if data.admin_pass != "Davolek":
        raise HTTPException(status_code=403, detail="Неверный пароль админа!")
    
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    
    if data.action == "badge":
        c.execute("UPDATE users SET badge = ? WHERE email = ?", (data.value, data.target_email))
    elif data.action == "stars":
        c.execute("UPDATE users SET stars = ? WHERE email = ?", (int(data.value), data.target_email))
    elif data.action == "status":
        c.execute("UPDATE users SET status = ? WHERE email = ?", (data.value, data.target_email))
        
    conn.commit()
    conn.close()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
