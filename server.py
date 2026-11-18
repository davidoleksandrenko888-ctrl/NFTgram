from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import random
import sqlite3
import os

app = FastAPI()

# --- БАЗА ДАННЫХ ---
def init_db():
    # Каждый раз удаляем старую базу, чтобы сбросить все пароли (чтобы не было путаницы)
    if os.path.exists('nftgram.db'):
        os.remove('nftgram.db')
        
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nickname TEXT UNIQUE, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '')''')
    # Создаем главного админа
    c.execute("INSERT INTO users (nickname, phone, password, status) VALUES (?, ?, ?, ?)",
              ("Admin", "+80000000000", "Davolek", "admin"))
    conn.commit()
    conn.close()

init_db()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
        body { background-color: #0e1621; color: white; font-family: 'Roboto', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; position: relative; overflow: hidden; }
        
        /* Снег на фоне */
        .snow { position: absolute; top: -10px; background: white; border-radius: 50%; opacity: 0.8; animation: fall linear infinite; }
        @keyframes fall { to { transform: translateY(100vh); } }

        .card { background-color: #17212b; padding: 30px; border-radius: 15px; text-align: center; width: 380px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); z-index: 10; position: relative; }
        h1 { color: #64b5f6; margin-bottom: 20px; font-weight: 500; }
        
        .input-group { position: relative; width: 100%; margin: 8px 0; }
        input { width: 100%; padding: 12px 14px; border-radius: 8px; border: 1px solid #242f3d; background-color: #242f3d; color: white; box-sizing: border-box; font-family: 'Roboto', sans-serif; outline: none; }
        input:focus { border-color: #64b5f6; }
        
        .eye-btn { position: absolute; right: 10px; top: 12px; cursor: pointer; color: #8b9eb0; font-size: 18px; user-select: none; }

        /* Выбор кода страны */
        .phone-select { width: 30%; background: #242f3d; color: white; border: 1px solid #242f3d; border-radius: 8px; padding: 12px; font-family: 'Roboto', sans-serif; outline: none; margin-right: 5px; }
        
        button { background-color: #64b5f6; color: #0e1621; border: none; padding: 14px; border-radius: 8px; font-weight: 500; cursor: pointer; width: 100%; margin-top: 15px; font-family: 'Roboto', sans-serif; transition: 0.2s; }
        button:hover { background-color: #42a5f5; }
        .link { color: #64b5f6; font-size: 14px; cursor: pointer; margin-top: 15px; display: block; text-decoration: underline; }
        .hidden { display: none; }

        .nav { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .nav button { width: auto; padding: 6px 12px; margin: 0; background: #242f3d; color: #8b9eb0; }
        .nav button.active { background: #64b5f6; color: #0e1621; }
        
        .admin-panel { border-top: 1px solid #333; margin-top: 20px; padding-top: 20px; text-align: left; }
        .badge { background: #e53935; padding: 2px 6px; border-radius: 5px; font-size: 11px; margin-left: 5px; }
    </style>
</head>
<body>
<div id="snow-container"></div>

<div class="card">
    <div class="nav">
        <button class="active" onclick="showLang('ru')">RU</button>
        <button onclick="showLang('uk')">UA</button>
        <button onclick="showLang('en')">EN</button>
    </div>
    
    <h1 id="title">NFTgram</h1>

    <!-- ЭКРАН ВХОДА -->
    <div id="loginScreen">
        <p class="sub" id="loginText">Войдите в свой аккаунт</p>
        <input type="text" id="loginNick" placeholder="Ваш Ник">
        <div class="input-group">
            <input type="password" id="loginPass" placeholder="Пароль">
            <span class="eye-btn" onclick="togglePass('loginPass', this)">👁️</span>
        </div>
        <button onclick="login()">Войти</button>
        <span class="link" onclick="showScreen('registerScreen')">Создать аккаунт</span>
    </div>

    <!-- ЭКРАН РЕГИСТРАЦИИ -->
    <div id="registerScreen" class="hidden">
        <p class="sub" id="regText">Регистрация нового аккаунта</p>
        <input type="text" id="regNick" placeholder="Придумайте Ник">
        <div class="input-group">
            <input type="password" id="regPass" placeholder="Придумайте Пароль">
            <span class="eye-btn" onclick="togglePass('regPass', this)">👁️</span>
        </div>
        <div class="input-group">
            <input type="password" id="regPass2" placeholder="Повторите Пароль">
            <span class="eye-btn" onclick="togglePass('regPass2', this)">👁️</span>
        </div>
        
        <div style="display: flex; align-items: center; margin-top: 10px;">
            <select class="phone-select" id="countryCode">
                <option value="+8">🇷🇺 +8</option>
                <option value="+380">🇺🇦 +380</option>
                <option value="+1">🇺🇸 +1</option>
            </select>
            <input type="text" id="regPhone" placeholder="Случайные цифры" value="Нажмите для генерации" readonly onclick="generatePhone()" style="cursor: pointer; color: #8b9eb0;">
        </div>
        
        <button onclick="register()">Зарегистрироваться</button>
        <span class="link" onclick="showScreen('loginScreen')">Уже есть аккаунт? Войти</span>
    </div>

    <!-- ПРОФИЛЬ -->
    <div id="profileScreen" class="hidden">
        <h2 id="profName">Имя</h2>
        <p id="profPhone" style="color: #64b5f6; font-size: 20px; margin: 5px 0;">+0000</p>
        <p id="profStatus" style="font-size: 14px; color: #8b9eb0;"></p>
        
        <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button style="background: #242f3d; color: white;" onclick="alert('Топы скоро!')">🏆 Топы</button>
            <button style="background: #242f3d; color: white;" onclick="alert('Кейсы скоро!')">🎁 Кейсы</button>
        </div>

        <div style="text-align: left; margin-top: 20px;">
            <label style="font-size: 12px; color: #8b9eb0;">Сменить имя:</label>
            <input type="text" id="newName">
            <label style="font-size: 12px; color: #8b9eb0;">Сменить номер:</label>
            <input type="text" id="newPhone">
            <button onclick="updateProfile()">Сохранить изменения</button>
        </div>

        <div class="admin-panel" id="adminPanel">
            <h3 style="color: #e53935;">Админ-панель</h3>
            <input type="text" id="adminTarget" placeholder="Ник пользователя">
            <select id="adminAction" style="width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; background: #242f3d; color: white; border: none;">
                <option value="badge">Выдать отметку (SCAM/FAKE)</option>
                <option value="stars">Дать звезды</option>
                <option value="status">Сделать админом</option>
            </select>
            <input type="text" id="adminValue" placeholder="Значение (SCAM, 9999, admin)">
            <button onclick="adminAction()" style="background: #e53935; color: white;">Выполнить</button>
        </div>
    </div>
</div>

<script>
    // Снег
    const snowContainer = document.getElementById('snow-container');
    for (let i = 0; i < 50; i++) {
        let snow = document.createElement('div');
        snow.className = 'snow';
        snow.style.left = Math.random() * 100 + 'vw';
        snow.style.width = snow.style.height = Math.random() * 5 + 2 + 'px';
        snow.style.animationDuration = Math.random() * 5 + 5 + 's';
        snow.style.animationDelay = Math.random() * 5 + 's';
        snowContainer.appendChild(snow);
    }

    function showScreen(id) {
        document.getElementById('loginScreen').classList.add('hidden');
        document.getElementById('registerScreen').classList.add('hidden');
        document.getElementById('profileScreen').classList.add('hidden');
        document.getElementById(id).classList.remove('hidden');
    }

    function togglePass(inputId, btn) {
        let input = document.getElementById(inputId);
        if (input.type === "password") { input.type = "text"; btn.innerText = "🙈"; } 
        else { input.type = "password"; btn.innerText = "👁️"; }
    }

    // Генерация случайного номера
    function generatePhone() {
        const code = document.getElementById('countryCode').value;
        const randomDigits = Math.floor(100000000 + Math.random() * 900000000);
        document.getElementById('regPhone').value = code + randomDigits;
    }

    // --- РЕГИСТРАЦИЯ ---
    async function register() {
        const nick = document.getElementById('regNick').value;
        const pass = document.getElementById('regPass').value;
        const pass2 = document.getElementById('regPass2').value;
        const phone = document.getElementById('regPhone').value;
        
        if (!nick || !pass || !pass2) return alert("Заполните все поля!");
        if (pass !== pass2) return alert("Пароли не совпадают!");
        if (phone === "Нажмите для генерации") return alert("Нажмите на поле номера, чтобы сгенерировать его!");
        
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: nick, password: pass, phone: phone})
        });
        
        if (res.ok) {
            alert("Аккаунт создан! Теперь войдите.");
            showScreen('loginScreen');
        } else {
            alert("Ошибка: этот Ник уже занят");
        }
    }

    // --- ВХОД ---
    async function login() {
        const nick = document.getElementById('loginNick').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: nick, password: pass})
        });
        if (res.ok) {
            const user = await res.json();
            showProfile(user);
        } else {
            alert("Неверный Ник или Пароль!");
        }
    }

    // --- ПРОФИЛЬ ---
    let currentUser = null;
    function showProfile(user) {
        currentUser = user;
        showScreen('profileScreen');
        document.getElementById('profName').innerText = user.nickname;
        document.getElementById('profPhone').innerText = user.phone;
        
        let badgeHtml = user.badge ? `<span class="badge">${user.badge}</span>` : '';
        document.getElementById('profStatus').innerHTML = `Статус: ${user.status} ${badgeHtml}`;

        if (user.status === 'admin' || user.password === 'Davolek') {
            document.getElementById('adminPanel').style.display = 'block';
        } else {
            document.getElementById('adminPanel').style.display = 'none';
        }
    }

    async function updateProfile() {
        const newName = document.getElementById('newName').value;
        const newPhone = document.getElementById('newPhone').value;
        if (!newName && !newPhone) return;

        await fetch('/api/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: currentUser.nickname, new_name: newName, new_phone: newPhone})
        });
        alert("Профиль обновлен!");
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
            body: JSON.stringify({admin_pass: currentUser.password, target_nick: target, action: action, value: value})
        });
        if (res.ok) { alert("Действие выполнено!"); } else { alert("Ошибка прав!"); }
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_PAGE

@app.post("/api/register")
def register_user(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (nickname, phone, password) VALUES (?, ?, ?)",
                  (data.get("nickname"), data.get("phone"), data.get("password")))
        conn.commit()
        return {"status": "ok"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ник занят")
    finally:
        conn.close()

@app.post("/api/login")
def login_user(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE nickname = ? AND password = ?", (data.get("nickname"), data.get("password")))
    user = c.fetchone()
    conn.close()
    if user:
        return {"nickname": user[1], "phone": user[2], "password": user[3], "status": user[5], "badge": user[6]}
    raise HTTPException(status_code=401, detail="Неверный Ник или Пароль")

@app.post("/api/update_profile")
def update_profile(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("new_name"): c.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (data.get("new_name"), data.get("nickname")))
    if data.get("new_phone"): c.execute("UPDATE users SET phone = ? WHERE nickname = ?", (data.get("new_phone"), data.get("nickname")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Davolek": raise HTTPException(status_code=403, detail="Неверный пароль админа!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("action") == "badge": c.execute("UPDATE users SET badge = ? WHERE nickname = ?", (data.get("value"), data.get("target_nick")))
    elif data.get("action") == "stars": c.execute("UPDATE users SET stars = ? WHERE nickname = ?", (int(data.get("value")), data.get("target_nick")))
    elif data.get("action") == "status": c.execute("UPDATE users SET status = ? WHERE nickname = ?", (data.get("value"), data.get("target_nick")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
