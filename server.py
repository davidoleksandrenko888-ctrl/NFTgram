from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
import sqlite3
import os
import shutil
from datetime import datetime

app = FastAPI()

# --- БАЗА ДАННЫХ ---
def init_db():
    # ❗ Я убрал os.remove('nftgram.db'), чтобы твоя база не удалялась при каждом запуске!
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nickname TEXT UNIQUE, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '', created_at TEXT, avatar TEXT DEFAULT '')''')
    
    # Проверяем, есть ли уже админ, чтобы не создавать его дубликаты
    c.execute("SELECT * FROM users WHERE nickname = 'Admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (nickname, phone, password, status, created_at) VALUES (?, ?, ?, ?, ?)",
                  ("Admin", "+80000000000", "Spyke", "admin", datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

init_db()

if not os.path.exists("avatars"):
    os.makedirs("avatars")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: #0e1621; color: white; font-family: 'Inter', sans-serif; height: 100vh; overflow: hidden; display: flex; }

        .snow { position: absolute; top: -10px; background: white; border-radius: 50%; opacity: 0.6; animation: fall linear infinite; pointer-events: none; z-index: 1;}
        @keyframes fall { to { transform: translateY(100vh); } }

        .auth-container { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; display: flex; justify-content: center; align-items: center; width: 100%; }
        .card { background-color: #17212b; padding: 40px; border-radius: 20px; width: 380px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); text-align: center; position: relative; }
        h1 { color: #64b5f6; margin-bottom: 20px; font-size: 28px; font-weight: 700; }
        .input-group { position: relative; width: 100%; margin: 10px 0; }
        input { width: 100%; padding: 14px 16px; border-radius: 12px; border: 1px solid #242f3d; background-color: #242f3d; color: white; font-family: 'Inter', sans-serif; outline: none; font-size: 14px; transition: 0.2s; }
        input:focus { border-color: #64b5f6; background: #1a2533; }
        .eye-btn { position: absolute; right: 15px; top: 14px; cursor: pointer; color: #8b9eb0; font-size: 18px; user-select: none; }
        button { background-color: #64b5f6; color: #0e1621; border: none; padding: 14px; border-radius: 12px; font-weight: 600; cursor: pointer; width: 100%; margin-top: 15px; font-family: 'Inter', sans-serif; transition: 0.2s; font-size: 15px; }
        button:hover { background-color: #42a5f5; transform: translateY(-1px); }
        .link { color: #64b5f6; font-size: 14px; cursor: pointer; margin-top: 15px; display: block; text-decoration: none; font-weight: 500; }
        .link:hover { text-decoration: underline; }
        .hidden { display: none !important; }

        #appScreen { display: none; width: 100%; height: 100%; background: #0e1621; z-index: 20; }
        
        .sidebar { width: 280px; background: #17212b; height: 100%; padding: 20px; border-right: 1px solid #242f3d; display: flex; flex-direction: column; }
        .profile-mini { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #242f3d; }
        
        .avatar { width: 80px; height: 80px; background: #242f3d; border-radius: 50%; margin: 0 auto 15px; display: flex; justify-content: center; align-items: center; font-size: 32px; color: #64b5f6; overflow: hidden; background-size: cover; background-position: center; }
        
        .user-name { font-size: 20px; font-weight: 600; margin-bottom: 5px; }
        .user-phone { color: #64b5f6; font-size: 14px; }
        .badge { background: #e53935; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; margin-left: 5px; }
        .user-stats { display: flex; justify-content: center; gap: 15px; margin-top: 15px; font-size: 13px; color: #8b9eb0; }
        .user-stats span { display: flex; align-items: center; gap: 5px; }

        .menu-item { padding: 14px 16px; border-radius: 10px; cursor: pointer; display: flex; align-items: center; gap: 10px; font-weight: 500; color: #8b9eb0; transition: 0.2s; margin-bottom: 5px; }
        .menu-item:hover, .menu-item.active { background: #242f3d; color: #64b5f6; }

        .content { flex: 1; padding: 40px; overflow-y: auto; position: relative; }
        .content-section { display: none; animation: fadeIn 0.3s; }
        .content-section.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        h2 { font-size: 28px; margin-bottom: 20px; }
        .card-box { background: #17212b; border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 1px solid #242f3d; }
        
        .admin-input { margin-bottom: 10px; }
        .btn-danger { background: #e53935; color: white; }
        .btn-danger:hover { background: #c62828; }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
        .case-item { background: #17212b; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #242f3d; transition: 0.2s; cursor: pointer; }
        .case-item:hover { border-color: #64b5f6; transform: translateY(-5px); }
        .case-img { font-size: 40px; margin-bottom: 10px; }
        
        .avatar-upload { display: none; }
        .avatar-label { cursor: pointer; color: #64b5f6; text-decoration: underline; font-size: 13px; }
    </style>
</head>
<body>
<div id="snow-container"></div>

<!-- ЭКРАН ВХОДА -->
<div class="auth-container" id="authScreen">
    <div class="card">
        <h1>NFTgram</h1>
        <p style="color: #8b9eb0; margin-bottom: 20px; font-size: 14px;" id="authSub">Войдите в свой аккаунт</p>
        
        <div id="loginForm">
            <div class="input-group"><input type="text" id="loginNick" placeholder="Ник"></div>
            <div class="input-group">
                <input type="password" id="loginPass" placeholder="Пароль">
                <span class="eye-btn" onclick="togglePass('loginPass', this)">👁️</span>
            </div>
            <button onclick="login()">Войти</button>
            <span class="link" onclick="showForm('register')">Создать аккаунт</span>
        </div>

        <div id="registerForm" class="hidden">
            <div class="input-group"><input type="text" id="regNick" placeholder="Придумайте Ник"></div>
            <div class="input-group">
                <input type="password" id="regPass" placeholder="Пароль">
                <span class="eye-btn" onclick="togglePass('regPass', this)">👁️</span>
            </div>
            <div class="input-group">
                <input type="password" id="regPass2" placeholder="Повторите пароль">
                <span class="eye-btn" onclick="togglePass('regPass2', this)">👁️</span>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <select id="countryCode" style="width: 35%; padding: 14px; border-radius: 12px; background: #242f3d; color: white; border: none; font-family: 'Inter';">
                    <option value="+8">🇷🇺 +8</option>
                    <option value="+380">🇺🇦 +380</option>
                    <option value="+1">🇺🇸 +1</option>
                </select>
                <input type="text" id="regPhone" placeholder="Номер (нажмите)" readonly onclick="generatePhone()" style="width: 65%; cursor: pointer; color: #8b9eb0;">
            </div>
            
            <button onclick="register()">Зарегистрироваться</button>
            <span class="link" onclick="showForm('login')">Уже есть аккаунт? Войти</span>
        </div>
    </div>
</div>

<!-- ГЛАВНОЕ ПРИЛОЖЕНИЕ -->
<div id="appScreen">
    <div class="sidebar">
        <div class="profile-mini">
            <div class="avatar" id="userAvatar">👤</div>
            <div class="user-name" id="sideName">Ник</div>
            <div class="user-phone" id="sidePhone">+0000</div>
            <div style="margin-top: 10px; font-size: 13px; color: #8b9eb0;">
                Статус: <span id="sideStatus">user</span>
                <span id="sideBadge"></span>
            </div>
            <div class="user-stats">
                <span>⭐ <span id="sideStars">1000</span></span>
                <span>📅 <span id="sideDays">0</span> дн.</span>
            </div>
        </div>

        <div class="menu-item active" onclick="switchTab('profile', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            Мой профиль
        </div>
        <div class="menu-item" onclick="switchTab('tops', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z"/></svg>
            Топы
        </div>
        <div class="menu-item" onclick="switchTab('cases', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76l1-1.36 1 1.36L15.38 12 17 10.83 14.92 8H20v6z"/></svg>
            Кейсы
        </div>
        <div class="menu-item" onclick="switchTab('auction', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
            Аукцион
        </div>
        <div class="menu-item" onclick="switchTab('nft', this)">
            <!-- Золотая иконка -->
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#FFD700"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            NFT
        </div>
        <div class="menu-item" onclick="switchTab('settings', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
            Настройки
        </div>
        
        <div style="margin-top: auto; padding-top: 20px;">
            <div class="menu-item" style="color: #e53935;" onclick="logout()">🚪 Выйти</div>
        </div>
    </div>

    <div class="content">
        <!-- ПРОФИЛЬ -->
        <div id="tab-profile" class="content-section active">
            <h2>Мой профиль</h2>
            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Информация об аккаунте</h3>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Ник: <strong id="profNick" style="color: white;"></strong></p>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Номер: <strong id="profPhone2" style="color: white;"></strong></p>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Дата создания: <strong id="profDate" style="color: white;"></strong></p>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Звезды: <strong id="profStars" style="color: #fbc02d;"></strong></p>
                <p style="color: #8b9eb0;">Отметка: <strong id="profBadge" style="color: #e53935;"></strong></p>
            </div>
        </div>

        <!-- ТОПЫ -->
        <div id="tab-tops" class="content-section">
            <h2>🏆 Топы</h2>
            <div class="grid">
                <div class="case-item" style="border-color: #fbc02d;">
                    <div class="case-img">🥇</div>
                    <h3>1 место</h3>
                    <p style="color: #8b9eb0; font-size: 13px;">GG1win (999k ⭐)</p>
                </div>
            </div>
        </div>

        <!-- КЕЙСЫ -->
        <div id="tab-cases" class="content-section">
            <h2>🎁 Кейсы</h2>
            <div class="grid">
                <div class="case-item" onclick="alert('Скоро!')"><div class="case-img">📦</div><h3>Обычный</h3><p>100 ⭐</p></div>
                <div class="case-item" onclick="alert('Скоро!')"><div class="case-img">🎁</div><h3>Редкий</h3><p>500 ⭐</p></div>
            </div>
        </div>

        <!-- АУКЦИОН -->
        <div id="tab-auction" class="content-section">
            <h2>⚖️ Аукцион</h2>
            <div class="card-box"><p style="color: #8b9eb0;">Тут будут лоты. Скоро!</p></div>
        </div>

        <!-- NFT -->
        <div id="tab-nft" class="content-section">
            <h2>🖼️ NFT</h2>
            <div class="card-box">
                <p style="color: #8b9eb0;">Здесь будут подарки из Telegram. Скоро!</p>
            </div>
        </div>

        <!-- НАСТРОЙКИ -->
        <div id="tab-settings" class="content-section">
            <h2>⚙️ Настройки</h2>
            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Аватар</h3>
                <input type="file" id="avatarUpload" class="avatar-upload" accept="image/*" onchange="uploadAvatar()">
                <label for="avatarUpload" class="avatar-label">Выбрать фото с компьютера</label>
            </div>
            
            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Смена имени и пароля</h3>
                <div class="input-group"><input type="text" id="newName" placeholder="Новый Ник"></div>
                <div class="input-group"><input type="password" id="newPass" placeholder="Новый Пароль"></div>
                <button onclick="updateProfile()">Сохранить изменения</button>
            </div>

            <div class="card-box" id="adminPanel" style="display: none; border-color: #e53935;">
                <h3 style="color: #e53935; margin-bottom: 15px;">Админ-панель (Spyke)</h3>
                <div class="input-group"><input type="text" id="adminTarget" placeholder="Ник пользователя"></div>
                <div class="input-group">
                    <select id="adminAction" style="width: 100%; padding: 14px; border-radius: 12px; background: #242f3d; color: white; border: none;">
                        <option value="badge">Выдать отметку</option>
                        <option value="stars">Дать звезды</option>
                        <option value="status">Сделать админом</option>
                    </select>
                </div>
                <div class="input-group"><input type="text" id="adminValue" placeholder="Значение"></div>
                <button class="btn-danger" onclick="adminAction()">Выполнить</button>
            </div>
        </div>
    </div>
</div>

<script>
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

    let currentUser = null;

    function togglePass(id, btn) {
        let input = document.getElementById(id);
        if (input.type === "password") { input.type = "text"; btn.innerText = "🙈"; } 
        else { input.type = "password"; btn.innerText = "👁️"; }
    }

    function showForm(form) {
        if (form === 'login') {
            document.getElementById('loginForm').classList.remove('hidden');
            document.getElementById('registerForm').classList.add('hidden');
            document.getElementById('authSub').innerText = "Войдите в свой аккаунт";
        } else {
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('registerForm').classList.remove('hidden');
            document.getElementById('authSub').innerText = "Регистрация";
        }
    }

    function generatePhone() {
        const code = document.getElementById('countryCode').value;
        const randomDigits = Math.floor(100000000 + Math.random() * 900000000);
        document.getElementById('regPhone').value = code + randomDigits;
    }

    async function register() {
        const nick = document.getElementById('regNick').value;
        const pass = document.getElementById('regPass').value;
        const pass2 = document.getElementById('regPass2').value;
        const phone = document.getElementById('regPhone').value;
        
        if (!nick || !pass || !pass2) return alert("Заполните все поля!");
        if (pass !== pass2) return alert("Пароли не совпадают!");
        if (phone === "Номер (нажмите)") return alert("Сгенерируйте номер!");
        
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: nick, password: pass, phone: phone})
        });
        
        if (res.ok) { alert("Аккаунт создан!"); showForm('login'); } 
        else { alert("Ошибка: Ник занят"); }
    }

    async function login() {
        const nick = document.getElementById('loginNick').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: nick, password: pass})
        });
        if (res.ok) {
            currentUser = await res.json();
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            updateUI();
        } else { alert("Неверный Ник или Пароль!"); }
    }

    function updateUI() {
        document.getElementById('sideName').innerText = currentUser.nickname;
        document.getElementById('sidePhone').innerText = currentUser.phone;
        document.getElementById('sideStatus').innerText = currentUser.status;
        document.getElementById('sideBadge').innerHTML = currentUser.badge ? `<span class="badge">${currentUser.badge}</span>` : '';
        document.getElementById('sideStars').innerText = currentUser.stars;
        
        const created = new Date(currentUser.created_at);
        const today = new Date();
        const diffTime = Math.abs(today - created);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        document.getElementById('sideDays').innerText = diffDays;

        document.getElementById('profNick').innerText = currentUser.nickname;
        document.getElementById('profPhone2').innerText = currentUser.phone;
        document.getElementById('profDate').innerText = currentUser.created_at;
        document.getElementById('profStars').innerText = currentUser.stars;
        document.getElementById('profBadge').innerText = currentUser.badge || 'Нет';

        // Аватар
        const avatarDiv = document.getElementById('userAvatar');
        if (currentUser.avatar) {
            avatarDiv.style.backgroundImage = `url(${currentUser.avatar})`;
            avatarDiv.innerText = "";
        } else {
            avatarDiv.style.backgroundImage = "none";
            avatarDiv.innerText = "👤";
        }

        if (currentUser.password === 'Spyke') { document.getElementById('adminPanel').style.display = 'block'; }
    }

    function switchTab(tabId, element) {
        document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
        if(element) element.classList.add('active');
        document.getElementById('tab-' + tabId).classList.add('active');
    }

    async function uploadAvatar() {
        const fileInput = document.getElementById('avatarUpload');
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("nickname", currentUser.nickname);

        const res = await fetch('/api/upload_avatar', { method: 'POST', body: formData });
        if (res.ok) {
            const data = await res.json();
            currentUser.avatar = data.avatar_url;
            updateUI();
            alert("Аватар обновлен!");
        } else { alert("Ошибка загрузки"); }
    }

    async function updateProfile() {
        const newName = document.getElementById('newName').value;
        const newPass = document.getElementById('newPass').value;
        
        const res = await fetch('/api/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: currentUser.nickname, new_name: newName, new_pass: newPass})
        });
        
        if (res.ok) {
            if (newName) currentUser.nickname = newName;
            if (newPass) currentUser.password = newPass;
            updateUI();
            alert("Данные изменены!");
        } else { alert("Ошибка изменения"); }
    }

    async function adminAction() {
        const target = document.getElementById('adminTarget').value;
        const action = document.getElementById('adminAction').value;
        const value = document.getElementById('adminValue').value;
        
        if (currentUser.password !== 'Spyke') return alert("Нет прав!");

        const res = await fetch('/api/admin_action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: currentUser.password, target_nick: target, action: action, value: value})
        });
        if (res.ok) { alert("Действие выполнено!"); } else { alert("Ошибка прав!"); }
    }

    function logout() { location.reload(); }
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
        c.execute("INSERT INTO users (nickname, phone, password, created_at) VALUES (?, ?, ?, ?)",
                  (data.get("nickname"), data.get("phone"), data.get("password"), datetime.now().strftime("%Y-%m-%d")))
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
        return {"nickname": user[1], "phone": user[2], "password": user[3], "stars": user[4], "status": user[5], "badge": user[6], "created_at": user[7], "avatar": user[8]}
    raise HTTPException(status_code=401, detail="Неверный Ник или Пароль")

@app.post("/api/upload_avatar")
async def upload_avatar(nickname: str, file: UploadFile = File(...)):
    file_location = f"avatars/{nickname}.png"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("UPDATE users SET avatar = ? WHERE nickname = ?", (file_location, nickname))
    conn.commit()
    conn.close()
    return {"avatar_url": file_location}

@app.post("/api/update_profile")
def update_profile(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("new_name"): c.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (data.get("new_name"), data.get("nickname")))
    if data.get("new_pass"): c.execute("UPDATE users SET password = ? WHERE nickname = ?", (data.get("new_pass"), data.get("nickname")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Spyke": raise HTTPException(status_code=403, detail="Неверный пароль админа!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("action") == "badge": 
        c.execute("UPDATE users SET badge = ? WHERE nickname = ?", (data.get("value"), data.get("target_nick")))
    elif data.get("action") == "stars": 
        c.execute("UPDATE users SET stars = ? WHERE nickname = ?", (int(data.get("value")), data.get("target_nick")))
    elif data.get("action") == "status": 
        # ВОТ ЗДЕСЬ БЫЛА ОШИБКА - добавил закрывающую скобку
        c.execute("UPDATE users SET status = ? WHERE nickname = ?", (data.get("value"), data.get("target_nick")))
    
    conn.commit()
    conn.close()
    return {"status": "ok"}
