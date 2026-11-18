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

# --- HTML САЙТ (НОВЫЙ ДИЗАЙН) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        body { 
            background-color: #0e1621; color: white; font-family: 'Inter', sans-serif; 
            display: flex; justify-content: center; align-items: center; 
            min-height: 100vh; margin: 0; 
        }
        .card { 
            background-color: #17212b; padding: 40px; border-radius: 20px; 
            text-align: center; width: 380px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        h1 { color: #64b5f6; margin-bottom: 10px; font-weight: 600; }
        p.sub { color: #8b9eb0; font-size: 14px; margin-bottom: 25px; }
        input { 
            width: 100%; padding: 14px; margin: 8px 0; border-radius: 10px; 
            border: 1px solid #242f3d; background-color: #242f3d; color: white; 
            box-sizing: border-box; font-family: 'Inter', sans-serif; outline: none;
        }
        input:focus { border-color: #64b5f6; }
        button { 
            background-color: #64b5f6; color: #0e1621; border: none; padding: 14px; 
            border-radius: 10px; font-weight: 600; cursor: pointer; width: 100%; 
            margin-top: 15px; font-family: 'Inter', sans-serif; transition: 0.2s;
        }
        button:hover { background-color: #42a5f5; }
        .google-btn { 
            background-color: white; color: #333; display: flex; 
            align-items: center; justify-content: center; gap: 10px; 
        }
        .google-btn:hover { background-color: #f1f1f1; }
        .link { color: #64b5f6; font-size: 14px; cursor: pointer; margin-top: 15px; display: block; text-decoration: underline; }
        .hidden { display: none; }
        .nav { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .nav button { width: auto; padding: 6px 12px; margin: 0; background: #242f3d; color: #8b9eb0; }
        .nav button.active { background: #64b5f6; color: #0e1621; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; }
        .modal-content { background: #17212b; padding: 30px; border-radius: 15px; width: 320px; text-align: center; }
        .admin-panel { border-top: 1px solid #333; margin-top: 20px; padding-top: 20px; text-align: left; }
        .badge { background: #e53935; padding: 2px 6px; border-radius: 5px; font-size: 11px; margin-left: 5px; }
    </style>
</head>
<body>
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
        <button class="google-btn" onclick="openGoogleModal()">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="18"> 
            Войти через Google
        </button>
        <div style="margin: 20px 0; border-bottom: 1px solid #242f3d;"></div>
        <input type="email" id="loginEmail" placeholder="Почта">
        <input type="password" id="loginPass" placeholder="Пароль">
        <button onclick="login()">Войти по паролю</button>
        <span class="link" onclick="showScreen('registerScreen')">Создать аккаунт</span>
    </div>

    <!-- ЭКРАН РЕГИСТРАЦИИ -->
    <div id="registerScreen" class="hidden">
        <p class="sub">Регистрация</p>
        <input type="text" id="regName" placeholder="Ваше имя (ник)">
        <input type="email" id="regEmail" placeholder="Почта (email)">
        <input type="password" id="regPass" placeholder="Пароль">
        <button onclick="register()">Зарегистрироваться</button>
        <span class="link" onclick="showScreen('loginScreen')">Уже есть аккаунт? Войти</span>
    </div>

    <!-- ПРОФИЛЬ -->
    <div id="profileScreen" class="hidden">
        <h2 id="profName">Имя</h2>
        <p id="profPhone" style="color: #64b5f6; font-size: 20px; margin: 5px 0;">+0000</p>
        <p id="profStatus" style="font-size: 14px; color: #8b9eb0;"></p>
        
        <!-- ТОПЫ И КЕЙСЫ (Заглушка) -->
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

        <!-- АДМИН ПАНЕЛЬ -->
        <div class="admin-panel" id="adminPanel">
            <h3 style="color: #e53935;">Админ-панель</h3>
            <input type="text" id="adminTarget" placeholder="Почта пользователя">
            <select id="adminAction" style="width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; background: #242f3d; color: white; border: none;">
                <option value="badge">Выдать отметку (SCAM/FAKE)</option>
                <option value="stars">Дать звезды</option>
                <option value="status">Сделать админом</option>
            </select>
            <input type="text" id="adminValue" placeholder="Значение (SCAM, 9999, admin)">
            <button onclick="adminAction()" style="background: #e53935; color: white;">Выполнить</button>
        </div>
    </div>
</div>

<!-- МОДАЛКА GOOGLE -->
<div id="googleModal" class="modal hidden">
    <div class="modal-content">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="40">
        <h3 style="margin: 15px 0;">Вход в аккаунт Google</h3>
        <input type="email" id="gEmail" placeholder="Введите почту Gmail">
        <input type="password" id="gPass" placeholder="Введите пароль">
        <button onclick="googleLogin()">Войти</button>
        <span class="link" onclick="closeGoogleModal()">Отмена</span>
    </div>
</div>

<script>
    function showScreen(id) {
        document.getElementById('loginScreen').classList.add('hidden');
        document.getElementById('registerScreen').classList.add('hidden');
        document.getElementById('profileScreen').classList.add('hidden');
        document.getElementById(id).classList.remove('hidden');
    }

    function openGoogleModal() { document.getElementById('googleModal').classList.remove('hidden'); }
    function closeGoogleModal() { document.getElementById('googleModal').classList.add('hidden'); }

    // --- ИМИТАЦИЯ ВХОДА ЧЕРЕЗ GOOGLE ---
    async function googleLogin() {
        const email = document.getElementById('gEmail').value;
        const pass = document.getElementById('gPass').value;
        if (!email || !pass) return alert("Введите почту и пароль!");

        const res = await fetch('/api/google_login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, password: pass})
        });
        
        if (res.ok) {
            const user = await res.json();
            showProfile(user);
            closeGoogleModal();
        } else {
            alert("Неверный пароль от Google!");
        }
    }

    // --- ОБЫЧНЫЙ ВХОД ---
    async function login() {
        const email = document.getElementById('loginEmail').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, password: pass})
        });
        if (res.ok) {
            const user = await res.json();
            showProfile(user);
        } else {
            alert("Неверная почта или пароль!");
        }
    }

    // --- РЕГИСТРАЦИЯ ---
    async function register() {
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const pass = document.getElementById('regPass').value;
        
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email, name: name, password: pass, lang: 'ru'})
        });
        
        if (res.ok) {
            const data = await res.json();
            alert(`Аккаунт создан! Ваш номер: ${data.phone}`);
            showScreen('loginScreen');
        } else {
            alert("Ошибка: этот email уже занят");
        }
    }

    // --- ПРОФИЛЬ ---
    let currentUser = null;
    function showProfile(user) {
        currentUser = user;
        showScreen('profileScreen');
        document.getElementById('profName').innerText = user.name;
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
            body: JSON.stringify({email: currentUser.email, new_name: newName, new_phone: newPhone})
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
            body: JSON.stringify({admin_pass: currentUser.password, target_email: target, action: action, value: value})
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

# --- API ЛОГИКА ---
@app.post("/api/google_login")
def google_login(data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password: raise HTTPException(status_code=400, detail="Пустые поля")
    
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    
    # Если пользователь есть, проверяем пароль (имитация)
    if user:
        if user[4] != password:
            conn.close()
            raise HTTPException(status_code=401, detail="Неверный пароль от Google")
        conn.close()
        return {"email": user[1], "name": user[2], "phone": user[3], "password": user[4], "status": user[6], "badge": user[7]}
    
    # Если нет — регистрируем
    phone = f"+8{random.randint(100000000, 999999999)}"
    name = email.split('@')[0]
    c.execute("INSERT INTO users (email, name, phone, password) VALUES (?, ?, ?, ?)",
              (email, name, phone, password))
    conn.commit()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return {"email": user[1], "name": user[2], "phone": user[3], "password": user[4], "status": user[6], "badge": user[7]}

@app.post("/api/register")
def register_user(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    try:
        phone = f"+8{random.randint(100000000, 999999999)}"
        c.execute("INSERT INTO users (email, name, phone, password) VALUES (?, ?, ?, ?)",
                  (data.get("email"), data.get("name"), phone, data.get("password")))
        conn.commit()
        return {"status": "ok", "phone": phone}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email занят")
    finally:
        conn.close()

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
    if data.get("new_name"): c.execute("UPDATE users SET name = ? WHERE email = ?", (data.get("new_name"), data.get("email")))
    if data.get("new_phone"): c.execute("UPDATE users SET phone = ? WHERE email = ?", (data.get("new_phone"), data.get("email")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Davolek": raise HTTPException(status_code=403, detail="Неверный пароль админа!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("action") == "badge": c.execute("UPDATE users SET badge = ? WHERE email = ?", (data.get("value"), data.get("target_email")))
    elif data.get("action") == "stars": c.execute("UPDATE users SET stars = ? WHERE email = ?", (int(data.get("value")), data.get("target_email")))
    elif data.get("action") == "status": c.execute("UPDATE users SET status = ? WHERE email = ?", (data.get("value"), data.get("target_email")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
