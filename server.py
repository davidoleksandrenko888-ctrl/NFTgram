from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
import os
import base64
from datetime import datetime

app = FastAPI()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nickname TEXT UNIQUE, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '', created_at TEXT, avatar TEXT DEFAULT '')''')
    
    c.execute("SELECT * FROM users WHERE nickname = 'Admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (nickname, phone, password, status, created_at) VALUES (?, ?, ?, ?, ?)",
                  ("Admin", "+80000000000", "Spyke", "admin", datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

init_db()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram ❄️</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background: linear-gradient(135deg, #0a111a 0%, #14212b 50%, #1a2a3a 100%); 
            color: white; font-family: 'Inter', sans-serif; height: 100vh; overflow: hidden; display: flex; 
        }

        /* СНЕГ */
        .snow { position: absolute; top: -10px; background: white; border-radius: 50%; opacity: 0.8; animation: fall linear infinite; pointer-events: none; z-index: 1; box-shadow: 0 0 10px rgba(255,255,255,0.5);}
        @keyframes fall { to { transform: translateY(100vh); } }

        /* АВТОРИЗАЦИЯ */
        .auth-container { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; display: flex; justify-content: center; align-items: center; width: 100%; }
        .card { 
            background: rgba(23, 33, 43, 0.8); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            padding: 40px; border-radius: 24px; width: 380px; box-shadow: 0 25px 50px rgba(0,0,0,0.8); 
            text-align: center; position: relative; border: 1px solid rgba(255,255,255,0.1); 
        }
        h1 { color: #90caf9; margin-bottom: 20px; font-size: 28px; font-weight: 700; text-shadow: 0 0 15px rgba(100,181,246,0.5); }
        .input-group { position: relative; width: 100%; margin: 10px 0; }
        input, select { 
            width: 100%; padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); 
            background: rgba(36, 47, 61, 0.7); color: white; font-family: 'Inter', sans-serif; outline: none; font-size: 14px; transition: 0.3s; 
        }
        input:focus { border-color: #90caf9; background: rgba(36, 47, 61, 0.9); box-shadow: 0 0 10px rgba(144,202,249,0.3); }
        .eye-btn { position: absolute; right: 15px; top: 14px; cursor: pointer; color: #8b9eb0; font-size: 18px; user-select: none; }
        button { 
            background: linear-gradient(135deg, #64b5f6, #42a5f5); color: #0e1621; border: none; padding: 14px; 
            border-radius: 12px; font-weight: 700; cursor: pointer; width: 100%; margin-top: 15px; 
            font-family: 'Inter', sans-serif; transition: 0.3s; font-size: 15px; box-shadow: 0 4px 15px rgba(100,181,246,0.4);
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(100,181,246,0.6); }
        .link { color: #90caf9; font-size: 14px; cursor: pointer; margin-top: 15px; display: block; text-decoration: none; font-weight: 500; }
        .link:hover { text-decoration: underline; }
        .hidden { display: none !important; }

        /* ГЛАВНОЕ ОКНО */
        #appScreen { display: none; width: 100%; height: 100%; z-index: 20; }
        
        .sidebar { 
            width: 280px; background: rgba(23, 33, 43, 0.7); backdrop-filter: blur(10px); 
            height: 100%; padding: 20px; border-right: 1px solid rgba(255,255,255,0.05); 
            display: flex; flex-direction: column; overflow-y: auto;
        }
        .profile-mini { text-align: center; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        
        .avatar { 
            width: 90px; height: 90px; background: rgba(36, 47, 61, 0.8); border-radius: 50%; margin: 0 auto 15px; 
            display: flex; justify-content: center; align-items: center; font-size: 40px; color: #64b5f6; 
            overflow: hidden; background-size: cover; background-position: center; border: 2px solid #64b5f6;
            box-shadow: 0 0 20px rgba(100,181,246,0.5);
        }
        
        .user-name { font-size: 20px; font-weight: 700; margin-bottom: 5px; }
        .user-phone { color: #90caf9; font-size: 14px; }
        .badge { background: #e53935; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-left: 5px; }
        .user-stats { display: flex; justify-content: center; gap: 15px; margin-top: 15px; font-size: 13px; color: #8b9eb0; }
        .user-stats span { display: flex; align-items: center; gap: 5px; }

        .menu-item { 
            padding: 14px 16px; border-radius: 12px; cursor: pointer; display: flex; align-items: center; 
            gap: 12px; font-weight: 500; color: #8b9eb0; transition: 0.3s; margin-bottom: 5px; 
        }
        .menu-item:hover, .menu-item.active { background: rgba(100,181,246,0.15); color: #90caf9; }

        .content { flex: 1; padding: 40px; overflow-y: auto; position: relative; }
        .content-section { display: none; animation: fadeIn 0.4s ease-out; }
        .content-section.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        h2 { font-size: 28px; margin-bottom: 20px; font-weight: 700; }
        .card-box { 
            background: rgba(23, 33, 43, 0.7); backdrop-filter: blur(10px); 
            border-radius: 20px; padding: 30px; margin-bottom: 20px; 
            border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .btn-danger { background: linear-gradient(135deg, #e53935, #c62828); color: white; box-shadow: 0 4px 15px rgba(229,57,53,0.4); }
        .btn-danger:hover { box-shadow: 0 6px 20px rgba(229,57,53,0.6); }

        /* СЕТКА ТОПОВ */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
        .case-item { 
            background: rgba(23, 33, 43, 0.7); border-radius: 20px; padding: 25px; 
            text-align: center; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; 
            cursor: pointer; position: relative; overflow: hidden;
        }
        .case-item:hover { border-color: #64b5f6; transform: translateY(-5px); box-shadow: 0 10px 25px rgba(100,181,246,0.2); }
        .case-img { font-size: 50px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(255,255,255,0.3)); }
        
        .avatar-upload { display: none; }
        .avatar-label { 
            cursor: pointer; color: #0e1621; background: #90caf9; padding: 10px 20px; 
            border-radius: 10px; font-size: 14px; font-weight: 600; display: inline-block; transition: 0.3s;
        }
        .avatar-label:hover { background: #64b5f6; box-shadow: 0 0 15px rgba(100,181,246,0.5); }
    </style>
</head>
<body>
<div id="snow-container"></div>

<!-- ЭКРАН ВХОДА -->
<div class="auth-container" id="authScreen">
    <div class="card">
        <h1>❄️ NFTgram</h1>
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
                <select id="countryCode">
                    <option value="+8">🇷🇺 +8</option>
                    <option value="+380">🇺🇦 +380</option>
                    <option value="+1">🇺🇸 +1</option>
                </select>
                <input type="text" id="regPhone" placeholder="Номер (нажмите)" readonly onclick="generatePhone()" style="cursor: pointer; color: #8b9eb0;">
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
                <span>❄️ <span id="sideDays">0</span> дн.</span>
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
            
            <div class="card-box" style="display: flex; align-items: center; gap: 30px;">
                <div class="avatar" style="width: 120px; height: 120px; margin: 0; font-size: 50px;" id="profileBigAvatar">👤</div>
                <div>
                    <h3 style="margin-bottom: 5px;" id="profNick"></h3>
                    <p style="color: #8b9eb0; margin-bottom: 15px;" id="profPhone2"></p>
                    <input type="file" id="avatarUpload" class="avatar-upload" accept="image/*" onchange="uploadAvatar()">
                    <label for="avatarUpload" class="avatar-label">Сменить аватар</label>
                </div>
            </div>

            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Статистика</h3>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Дата создания: <strong id="profDate" style="color: white;"></strong></p>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Звезды: <strong id="profStars" style="color: #fbc02d;"></strong></p>
                <p style="color: #8b9eb0;">Отметка: <strong id="profBadge" style="color: #e53935;"></strong></p>
            </div>

            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Изменить данные</h3>
                <div class="input-group"><input type="text" id="newName" placeholder="Новый Ник"></div>
                <div class="input-group"><input type="password" id="newPass" placeholder="Новый Пароль"></div>
                <button onclick="updateProfile()">Сохранить изменения</button>
            </div>
        </div>

        <!-- ТОПЫ -->
        <div id="tab-tops" class="content-section">
            <h2>🏆 Топы</h2>
            <div class="grid" id="topUsersList"></div>
        </div>

        <!-- КЕЙСЫ -->
        <div id="tab-cases" class="content-section">
            <h2>🎁 Кейсы</h2>
            <div class="grid">
                <div class="case-item" onclick="alert('Скоро!')"><div class="case-img">📦</div><h3>Обычный</h3><p style="color:#64b5f6; font-weight:600; margin-top:5px;">100 ⭐</p></div>
                <div class="case-item" onclick="alert('Скоро!')"><div class="case-img">🎁</div><h3>Редкий</h3><p style="color:#e53935; font-weight:600; margin-top:5px;">500 ⭐</p></div>
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

        <!-- НАСТРОЙКИ И АДМИНКА -->
        <div id="tab-settings" class="content-section">
            <h2>⚙️ Настройки</h2>
            
            <div class="card-box" id="adminPanel" style="display: none; border-color: #e53935;">
                <h3 style="color: #e53935; margin-bottom: 15px;">Админ-панель (Spyke)</h3>
                <div class="input-group"><input type="text" id="adminTarget" placeholder="Ник пользователя"></div>
                <div class="input-group">
                    <select id="adminAction">
                        <option value="badge">Выдать отметку</option>
                        <option value="stars">Дать звезды</option>
                        <option value="status">Сделать админом</option>
                    </select>
                </div>
                <div class="input-group"><input type="text" id="adminValue" placeholder="Значение"></div>
                <button class="btn-danger" onclick="adminAction()">Выполнить</button>
            </div>
            
            <div class="card-box" style="text-align: center; color: #8b9eb0;">
                <p>Версия NFTgram Winter Edition 1.0</p>
            </div>
        </div>
    </div>
</div>

<script>
    // СНЕГ
    const snowContainer = document.getElementById('snow-container');
    for (let i = 0; i < 70; i++) {
        let snow = document.createElement('div');
        snow.className = 'snow';
        snow.style.left = Math.random() * 100 + 'vw';
        let size = Math.random() * 6 + 2;
        snow.style.width = snow.style.height = size + 'px';
        snow.style.animationDuration = Math.random() * 5 + 5 + 's';
        snow.style.animationDelay = Math.random() * 5 + 's';
        snow.style.opacity = Math.random() * 0.5 + 0.3;
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
        document.getElementById('sideDays').innerText = diffDays || 1;

        document.getElementById('profNick').innerText = currentUser.nickname;
        document.getElementById('profPhone2').innerText = currentUser.phone;
        document.getElementById('profDate').innerText = currentUser.created_at;
        document.getElementById('profStars').innerText = currentUser.stars;
        document.getElementById('profBadge').innerText = currentUser.badge || 'Нет';

        // АВАТАРКИ
        const avatarImg = currentUser.avatar ? `<img src="${currentUser.avatar}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">` : "👤";
        document.getElementById('userAvatar').innerHTML = avatarImg;
        document.getElementById('profileBigAvatar').innerHTML = avatarImg;

        // АДМИНКА
        if (currentUser.password === 'Spyke' || currentUser.status === 'admin') { 
            document.getElementById('adminPanel').style.display = 'block'; 
        } else {
            document.getElementById('adminPanel').style.display = 'none'; 
        }
    }

    function switchTab(tabId, element) {
        document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
        if(element) element.classList.add('active');
        document.getElementById('tab-' + tabId).classList.add('active');

        if(tabId === 'tops') {
            loadTops();
        }
    }

    async function loadTops() {
        const res = await fetch('/api/tops');
        if(res.ok) {
            const users = await res.json();
            const container = document.getElementById('topUsersList');
            container.innerHTML = '';
            
            users.forEach((u, index) => {
                let medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅';
                let avatarImg = u.avatar ? `<img src="${u.avatar}" style="width:50px; height:50px; object-fit:cover; border-radius:50%; margin-bottom:10px; border: 2px solid #64b5f6;">` : `<div style="font-size:40px; margin-bottom:10px;">👤</div>`;
                
                container.innerHTML += `
                    <div class="case-item" style="border-color: ${index === 0 ? '#fbc02d' : 'rgba(255,255,255,0.05)'};">
                        <div class="case-img">${medal}</div>
                        ${avatarImg}
                        <h3>${u.nickname}</h3>
                        <p style="color: #fbc02d; font-weight:600; font-size: 14px; margin-top: 5px;">${u.stars} ⭐</p>
                    </div>
                `;
            });
        }
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
        } else { alert("Ошибка загрузки. Попробуйте фото поменьше."); }
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
        
        if (currentUser.password !== 'Spyke' && currentUser.status !== 'admin') return alert("Нет прав!");

        const res = await fetch('/api/admin_action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: currentUser.password, target_nick: target, action: action, value: value})
        });
        if (res.ok) { alert("Действие выполнено!"); } else { alert("Ошибка выполнения!"); }
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
async def upload_avatar(nickname: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    # Конвертируем картинку в Base64 (сохраняем в БД, чтобы не пропала)
    encoded_string = base64.b64encode(contents).decode('utf-8')
    mime_type = file.content_type
    base64_url = f"data:{mime_type};base64,{encoded_string}"
    
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("UPDATE users SET avatar = ? WHERE nickname = ?", (base64_url, nickname))
    conn.commit()
    conn.close()
    return {"avatar_url": base64_url}

@app.post("/api/update_profile")
def update_profile(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("new_name"): c.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (data.get("new_name"), data.get("nickname")))
    if data.get("new_pass"): c.execute("UPDATE users SET password = ? WHERE nickname = ?", (data.get("new_pass"), data.get("nickname")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/tops")
def get_tops():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT nickname, stars, avatar, badge FROM users ORDER BY stars DESC LIMIT 10")
    users = c.fetchall()
    conn.close()
    return [{"nickname": u[0], "stars": u[1], "avatar": u[2], "badge": u[3]} for u in users]

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
        c.execute("UPDATE users SET status = ? WHERE nickname = ?", (data.get("value"), data.get("target_nick")))
    
    conn.commit()
    conn.close()
    return {"status": "ok"}
