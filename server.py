from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import sqlite3
import os
import base64
import random
from datetime import datetime

app = FastAPI()

def init_db():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nickname TEXT UNIQUE, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '', created_at TEXT, avatar TEXT DEFAULT '',
                 role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0,
                 username TEXT UNIQUE, custom_id TEXT UNIQUE, bio TEXT DEFAULT '')''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        c.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN username TEXT")
        c.execute("ALTER TABLE users ADD COLUMN custom_id TEXT")
        c.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    c.execute("SELECT * FROM users WHERE nickname = 'Admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (nickname, phone, password, username, custom_id, stars, role, created_at, bio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  ("Admin", "+79999999999", "spyke", "@admin_bot", "0000000000", 999999, "owner", datetime.now().strftime("%Y-%m-%d"), "Системный аккаунт"))
    
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background: linear-gradient(135deg, #0a111a 0%, #14212b 50%, #1a2a3a 100%); 
            color: white; font-family: 'Inter', sans-serif; height: 100vh; overflow: hidden; display: flex; 
        }

        .snow { position: absolute; top: -10px; background: white; border-radius: 50%; opacity: 0.8; animation: fall linear infinite; pointer-events: none; z-index: 1; box-shadow: 0 0 10px rgba(255,255,255,0.5);}
        @keyframes fall { to { transform: translateY(100vh); } }

        /* КРАСИВЫЕ УВЕДОМЛЕНИЯ */
        #toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 15px; align-items: flex-end; pointer-events: none; }
        .toast { 
            background: rgba(23, 33, 43, 0.95); backdrop-filter: blur(15px); color: white; 
            padding: 15px 25px; border-radius: 15px; font-weight: 600; font-size: 14px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.8); border: 1px solid rgba(100,181,246,0.3);
            animation: slideIn 0.3s forwards;
            display: flex; align-items: center; gap: 10px; pointer-events: auto;
        }
        .toast.success { border-color: #43a047; box-shadow: 0 0 15px rgba(67,160,71,0.3); }
        .toast.error { border-color: #e53935; box-shadow: 0 0 15px rgba(229,57,53,0.3); }
        @keyframes slideIn { from { opacity: 0; transform: translateX(50px); } to { opacity: 1; transform: translateX(0); } }

        .auth-container { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10; display: flex; justify-content: center; align-items: center; width: 100%; }
        .card { 
            background: rgba(23, 33, 43, 0.8); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
            padding: 40px; border-radius: 24px; width: 380px; box-shadow: 0 25px 50px rgba(0,0,0,0.8); 
            text-align: center; position: relative; border: 1px solid rgba(255,255,255,0.1); 
        }
        h1 { color: #90caf9; margin-bottom: 20px; font-size: 28px; font-weight: 800; text-shadow: 0 0 15px rgba(100,181,246,0.5); }
        .input-group { position: relative; width: 100%; margin: 10px 0; }
        input, textarea, select { 
            width: 100%; padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); 
            background: rgba(36, 47, 61, 0.7); color: white; font-family: 'Inter', sans-serif; outline: none; font-size: 14px; transition: 0.3s; 
        }
        input:focus, textarea:focus, select:focus { border-color: #90caf9; background: rgba(36, 47, 61, 0.9); box-shadow: 0 0 10px rgba(144,202,249,0.3); }
        select option { background: #17212b; color: white; }
        textarea { resize: vertical; min-height: 80px; }
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
        
        .user-name { font-size: 20px; font-weight: 700; margin-bottom: 2px; display: flex; justify-content: center; align-items: center; gap: 5px;}
        .user-id-text { font-size: 12px; color: #8b9eb0; margin-bottom: 5px; }
        .user-phone { color: #90caf9; font-size: 14px; font-weight: 500; }
        
        .menu-item { 
            padding: 14px 16px; border-radius: 12px; cursor: pointer; display: flex; align-items: center; 
            gap: 12px; font-weight: 500; color: #8b9eb0; transition: 0.3s; margin-bottom: 5px; 
        }
        .menu-item:hover, .menu-item.active { background: rgba(100,181,246,0.15); color: #90caf9; }
        .menu-item svg { fill: currentColor; }

        .content { flex: 1; padding: 40px; overflow-y: auto; position: relative; }
        .content-section { display: none; animation: fadeIn 0.4s ease-out; }
        .content-section.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        h2 { font-size: 28px; margin-bottom: 20px; font-weight: 800; }
        .card-box { 
            background: rgba(23, 33, 43, 0.7); backdrop-filter: blur(10px); 
            border-radius: 20px; padding: 30px; margin-bottom: 20px; 
            border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .btn-danger { background: linear-gradient(135deg, #e53935, #c62828); color: white; box-shadow: 0 4px 15px rgba(229,57,53,0.4); }
        .btn-danger:hover { box-shadow: 0 6px 20px rgba(229,57,53,0.6); }
        .btn-success { background: linear-gradient(135deg, #43a047, #2e7d32); color: white; box-shadow: 0 4px 15px rgba(67,160,71,0.4); }
        
        .admin-btn-group { display: flex; gap: 10px; margin-top: 15px; }
        .admin-btn-group button { margin-top: 0; }

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

        .role-badge { font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 6px; letter-spacing: 0.5px; display: inline-block; }
        .role-owner { color: #e53935; border: 1px solid #e53935; background: rgba(229,57,53,0.1); }
        .role-admin { color: #ff9800; border: 1px solid #ff9800; background: rgba(255,152,0,0.1); }
        .role-moder { color: #4caf50; border: 1px solid #4caf50; background: rgba(76,175,80,0.1); }
        .role-helper { color: #00bcd4; border: 1px solid #00bcd4; background: rgba(0,188,212,0.1); }
        .role-scam { color: #9e9e9e; border: 1px solid #9e9e9e; text-decoration: line-through; }

        .admin-section {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(100,181,246,0.2);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
        }
        .admin-section::before {
            content: '❄️';
            position: absolute;
            top: -10px;
            left: 20px;
            background: #17212b;
            padding: 0 5px;
            font-size: 16px;
        }
        .admin-title { color: #90caf9; font-size: 16px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;}

        /* МОДАЛЬНОЕ ОКНО ПРОСМОТРА ПРОФИЛЯ */
        #viewProfileModal {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); backdrop-filter: blur(5px);
            display: none; justify-content: center; align-items: center; z-index: 1000;
        }
        .view-profile-card {
            background: rgba(23, 33, 43, 0.95); border: 1px solid rgba(100,181,246,0.3);
            padding: 40px; border-radius: 20px; text-align: center; width: 350px;
            box-shadow: 0 0 50px rgba(0,0,0,0.8);
        }
        .view-profile-card .avatar { width: 120px; height: 120px; font-size: 50px; border-color: #90caf9; }
    </style>
</head>
<body>
<div id="snow-container"></div>
<div id="toast-container"></div>

<!-- МОДАЛКА ПРОСМОТРА ПРОФИЛЯ -->
<div id="viewProfileModal" onclick="closeViewProfile(event)">
    <div class="view-profile-card" onclick="event.stopPropagation()">
        <div class="avatar" id="viewAvatar">👤</div>
        <h3 style="margin-bottom: 5px;" id="viewNick">Ник</h3>
        <p style="color: #90caf9; font-weight: 600; margin-bottom: 5px;" id="viewUsername">@username</p>
        <p style="color: #8b9eb0; font-size: 13px; margin-bottom: 10px;" id="viewId">ID: 0</p>
        <p style="color: #b0bec5; font-size: 14px; font-style: italic; margin-bottom: 15px;" id="viewBio">Био</p>
        <p style="color: #fbc02d; font-weight: 700;" id="viewStars">0 ⭐</p>
        <button style="margin-top: 20px; background: #e53935; color: white;" onclick="closeViewProfile()">Закрыть</button>
    </div>
</div>

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
            <div class="input-group"><input type="text" id="regNick" placeholder="Имя (Nickname)"></div>
            <div class="input-group">
                <input type="password" id="regPass" placeholder="Пароль">
                <span class="eye-btn" onclick="togglePass('regPass', this)">👁️</span>
            </div>
            <div class="input-group">
                <input type="password" id="regPass2" placeholder="Повторите пароль">
                <span class="eye-btn" onclick="togglePass('regPass2', this)">👁️</span>
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
            <div class="user-id-text" id="sideId">ID: 0</div>
            <div class="user-phone" id="sideUser">@username</div>
            <div class="user-stats" style="margin-top: 10px; font-size: 13px; color: #8b9eb0; display: flex; justify-content: center; gap: 10px;">
                <span>⭐ <span id="sideStars">1000</span></span>
                <span>❄️ <span id="sideDays">0</span> дн.</span>
            </div>
        </div>

        <div class="menu-item active" onclick="switchTab('profile', this)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            Мой профиль
        </div>
        <div class="menu-item" onclick="switchTab('tops', this)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z"/></svg>
            Топы
        </div>
        <div class="menu-item" onclick="switchTab('cases', this)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2z"/></svg>
            Кейсы
        </div>
        <div class="menu-item" onclick="switchTab('auction', this)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
            Аукцион
        </div>
        <div class="menu-item" onclick="switchTab('nft', this)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#FFD700"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            NFT
        </div>
        <div class="menu-item" onclick="switchTab('settings', this)">
            <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
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
                    <h3 style="margin-bottom: 5px; display: flex; align-items: center; gap: 8px;" id="profNick"></h3>
                    <p style="color: #90caf9; font-weight: 600; margin-bottom: 2px;" id="profUser"></p>
                    <p style="color: #8b9eb0; font-size: 13px; margin-bottom: 10px;" id="profId"></p>
                    <p style="color: #b0bec5; font-size: 14px; font-style: italic; margin-bottom: 15px;" id="profBio"></p>
                    <input type="file" id="avatarUpload" class="avatar-upload" accept="image/*" onchange="uploadAvatar()">
                    <label for="avatarUpload" class="avatar-label">Сменить аватар</label>
                </div>
            </div>

            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Статистика</h3>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Дата создания: <strong id="profDate" style="color: white;"></strong></p>
                <p style="margin-bottom: 10px; color: #8b9eb0;">Звезды: <strong id="profStars" style="color: #fbc02d;"></strong></p>
            </div>

            <div class="card-box">
                <h3 style="margin-bottom: 15px;">Изменить данные</h3>
                <div class="input-group"><input type="text" id="newName" placeholder="Новое Имя"></div>
                <div class="input-group"><input type="text" id="newUsername" placeholder="Новый Юзернейм (без @, англ)"></div>
                <div class="input-group"><textarea id="newBio" placeholder="О себе (Био)"></textarea></div>
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
                <div class="case-item" onclick="showToast('Скоро!', 'error')"><div class="case-img">📦</div><h3>Обычный</h3><p style="color:#64b5f6; font-weight:600; margin-top:5px;">100 ⭐</p></div>
                <div class="case-item" onclick="showToast('Скоро!', 'error')"><div class="case-img">🎁</div><h3>Редкий</h3><p style="color:#e53935; font-weight:600; margin-top:5px;">500 ⭐</p></div>
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
            
            <div class="card-box" id="adminPasswordForm">
                <h3 style="margin-bottom: 15px;">Панель управления</h3>
                <p style="color: #8b9eb0; margin-bottom: 10px; font-size: 14px;">Введите пароль администратора для доступа к скрытым функциям.</p>
                <div class="input-group"><input type="password" id="adminPassInput" placeholder="Пароль"></div>
                <button onclick="checkAdminPass()">Активировать</button>
            </div>

            <div id="adminPanel" style="display: none;">
                <div class="admin-section">
                    <div class="admin-title">❄️ Выдать звезды</div>
                    <div class="input-group"><input type="text" id="adminTargetStars" placeholder="ID пользователя"></div>
                    <div class="input-group"><input type="number" id="adminValueStars" placeholder="Кол-во звезд"></div>
                    <button class="btn-success" onclick="adminAction('stars')">Выдать</button>
                </div>

                <div class="admin-section">
                    <div class="admin-title">❄️ Сменить роль</div>
                    <div class="input-group"><input type="text" id="adminTargetRole" placeholder="ID пользователя"></div>
                    <div class="input-group">
                        <select id="adminValueRole">
                            <option value="owner">Овнер 👑</option>
                            <option value="admin">Админ 🛡️</option>
                            <option value="moder">Модер ⚔️</option>
                            <option value="helper">Хелпер 💠</option>
                            <option value="scam">Скам 🚫</option>
                            <option value="user">Юзер 👤 (Сброс)</option>
                        </select>
                    </div>
                    <button onclick="adminAction('role')">Сменить роль</button>
                </div>

                <div class="admin-section">
                    <div class="admin-title">❄️ Бан / Разбан</div>
                    <div class="input-group"><input type="text" id="adminTargetBan" placeholder="ID пользователя"></div>
                    <div class="admin-btn-group">
                        <button class="btn-danger" onclick="adminAction('ban', 1)">Забанить</button>
                        <button class="btn-success" onclick="adminAction('ban', 0)">Разбанить</button>
                    </div>
                </div>
            </div>
            
            <div class="card-box" style="text-align: center; color: #8b9eb0; margin-top: 50px;">
                <p>Версия NFTgram Winter Edition 1.7</p>
            </div>
        </div>
    </div>
</div>

<script>
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

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${type === 'success' ? '✅' : '❌'}</span> ${message}`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = '0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

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

    window.onload = function() {
        const savedUser = localStorage.getItem('nftgram_user');
        if (savedUser) {
            currentUser = JSON.parse(savedUser);
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            updateUI();
        }
    };

    async function register() {
        const nick = document.getElementById('regNick').value;
        const pass = document.getElementById('regPass').value;
        const pass2 = document.getElementById('regPass2').value;
        
        if (!nick || !pass) return showToast("Заполните все поля!", "error");
        if (pass !== pass2) return showToast("Пароли не совпадают!", "error");
        
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: nick, password: pass})
        });
        
        if (res.ok) { 
            showToast("Регистрация успешна!", "success"); 
            setTimeout(() => showForm('login'), 1500);
        } 
        else { showToast("Ошибка: Ник занят", "error"); }
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
            const data = await res.json();
            if(data.error) return showToast(data.error, "error");
            
            currentUser = data;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            updateUI();
            showToast("С возвращением!", "success");
        } else { showToast("Неверный Ник или Пароль!", "error"); }
    }

    function updateUI() {
        document.getElementById('sideName').innerHTML = `${currentUser.nickname}`;
        document.getElementById('sideId').innerText = `ID: ${currentUser.custom_id}`;
        document.getElementById('sideUser').innerText = currentUser.username;
        document.getElementById('sideStars').innerText = currentUser.stars;
        
        const created = new Date(currentUser.created_at);
        const diffTime = Math.abs(new Date() - created);
        document.getElementById('sideDays').innerText = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) || 1;

        document.getElementById('profNick').innerHTML = `${currentUser.nickname}`;
        document.getElementById('profUser').innerText = currentUser.username;
        document.getElementById('profId').innerText = `Ваш ID: ${currentUser.custom_id}`;
        document.getElementById('profBio').innerText = currentUser.bio || 'Био пока нет...';
        document.getElementById('profDate').innerText = currentUser.created_at;
        document.getElementById('profStars').innerText = currentUser.stars;

        const avatarImg = currentUser.avatar ? `<img src="${currentUser.avatar}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">` : "👤";
        document.getElementById('userAvatar').innerHTML = avatarImg;
        document.getElementById('profileBigAvatar').innerHTML = avatarImg;

        const roleMap = {
            "owner": { text: "OWNER", class: "role-owner" },
            "admin": { text: "ADMIN", class: "role-admin" },
            "moder": { text: "MODER", class: "role-moder" },
            "helper": { text: "HELPER", class: "role-helper" },
            "scam": { text: "SCAM", class: "role-scam" }
        };

        if (roleMap[currentUser.role]) {
            const r = roleMap[currentUser.role];
            document.getElementById('sideName').innerHTML = `${currentUser.nickname} <span class="role-badge ${r.class}">[${r.text}]</span>`;
            document.getElementById('profNick').innerHTML = `${currentUser.nickname} <span class="role-badge ${r.class}">[${r.text}]</span>`;
        }
    }

    function switchTab(tabId, element) {
        document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
        if(element) element.classList.add('active');
        document.getElementById('tab-' + tabId).classList.add('active');
        if(tabId === 'tops') loadTops();
    }

    async function loadTops() {
        const res = await fetch('/api/tops');
        if(res.ok) {
            const users = await res.json();
            const container = document.getElementById('topUsersList');
            container.innerHTML = '';
            
            users.forEach((u, index) => {
                let medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅';
                let avatarImg = u.avatar ? `<img src="${u.avatar}" style="width:60px; height:60px; object-fit:cover; border-radius:50%; margin-bottom:10px; border: 2px solid #64b5f6;">` : `<div style="font-size:40px; margin-bottom:10px;">👤</div>`;
                
                // ДОБАВИЛ ONCLICK ДЛЯ ПРОСМОТРА ПРОФИЛЯ
                container.innerHTML += `
                    <div class="case-item" style="border-color: ${index === 0 ? '#fbc02d' : 'rgba(255,255,255,0.05)'};" onclick='openViewProfile(${JSON.stringify(u)})'>
                        <div class="case-img">${medal}</div>
                        ${avatarImg}
                        <h3 style="display: flex; justify-content: center; align-items: center; gap: 5px;">${u.nickname}</h3>
                        <p style="color: #fbc02d; font-weight:700; font-size: 15px; margin-top: 5px;">${u.stars} ⭐</p>
                    </div>
                `;
            });
        }
    }

    // ПРОСМОТР ЧУЖОГО ПРОФИЛЯ
    function openViewProfile(user) {
        document.getElementById('viewNick').innerText = user.nickname;
        document.getElementById('viewUsername').innerText = user.username || '@нет';
        document.getElementById('viewId').innerText = `ID: ${user.custom_id || 'нет'}`;
        document.getElementById('viewBio').innerText = user.bio || 'Био пока нет...';
        document.getElementById('viewStars').innerText = `${user.stars} ⭐`;
        
        const avatarDiv = document.getElementById('viewAvatar');
        if (user.avatar) {
            avatarDiv.innerHTML = `<img src="${user.avatar}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
        } else {
            avatarDiv.innerHTML = "👤";
        }
        
        document.getElementById('viewProfileModal').style.display = 'flex';
    }

    function closeViewProfile(e) {
        if (e && e.target.id !== 'viewProfileModal' && e.target.tagName !== 'BUTTON') return;
        document.getElementById('viewProfileModal').style.display = 'none';
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
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            updateUI();
            showToast("Аватар обновлен!", "success");
        } else { showToast("Ошибка загрузки. Фото слишком большое.", "error"); }
    }

    async function updateProfile() {
        const newName = document.getElementById('newName').value;
        const newUser = document.getElementById('newUsername').value;
        const newBio = document.getElementById('newBio').value;
        const newPass = document.getElementById('newPass').value;
        
        if (newUser && !/^[a-zA-Z0-9_]+$/.test(newUser)) {
            return showToast("Юзернейм только на английском!", "error");
        }

        const res = await fetch('/api/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                nickname: currentUser.nickname, 
                new_name: newName, 
                new_username: newUser ? "@" + newUser : null, 
                new_bio: newBio, 
                new_pass: newPass
            })
        });
        
        if (res.ok) {
            if (newName) currentUser.nickname = newName;
            if (newUser) currentUser.username = "@" + newUser;
            if (newBio) currentUser.bio = newBio;
            if (newPass) currentUser.password = newPass;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            updateUI();
            showToast("Данные изменены!", "success");
        } else { showToast("Ошибка изменения", "error"); }
    }

    function checkAdminPass() {
        const pass = document.getElementById('adminPassInput').value;
        if (pass === 'Spyke') {
            document.getElementById('adminPasswordForm').style.display = 'none';
            document.getElementById('adminPanel').style.display = 'block';
            showToast("Админка разблокирована!", "success");
        } else {
            showToast("Неверный пароль!", "error");
        }
    }

    // ОБНОВЛЕННАЯ АДМИНКА (МГНОВЕННО ОБНОВЛЯЕТ ДАННЫЕ)
    async function adminAction(action, forceValue = null) {
        let targetId = '';
        let value = forceValue;

        if (action === 'stars') {
            targetId = document.getElementById('adminTargetStars').value;
            value = document.getElementById('adminValueStars').value;
        } else if (action === 'role') {
            targetId = document.getElementById('adminTargetRole').value;
            value = document.getElementById('adminValueRole').value;
        } else if (action === 'ban') {
            targetId = document.getElementById('adminTargetBan').value;
        }

        if(!targetId) return showToast("Введите ID пользователя!", "error");
        if (value === null || value === '') return showToast("Заполните значение!", "error");

        const res = await fetch('/api/admin_action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: "Spyke", target_id: targetId, action: action, value: value})
        });
        
        if (res.ok) { 
            showToast("Действие выполнено!", "success"); 
            
            // Если мы изменили СВОЙ профиль, обновляем локальные данные
            if (targetId === currentUser.custom_id) {
                if (action === 'stars') currentUser.stars = parseInt(value);
                if (action === 'role') currentUser.role = value;
                localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
                updateUI();
            }
            if (action === 'stars' || action === 'role') loadTops(); // Обновляем топы

        } 
        else { showToast("Ошибка! Проверьте правильность ID.", "error"); }
    }

    function logout() { 
        localStorage.removeItem('nftgram_user');
        location.reload(); 
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
    
    random_phone = f"+7{random.randint(9000000000, 9999999999)}"
    random_username = f"@user{random.randint(1000, 9999)}"
    random_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    
    try:
        c.execute("INSERT INTO users (nickname, phone, password, username, custom_id, stars, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (data.get("nickname"), random_phone, data.get("password"), random_username, random_id, 1000, "user", datetime.now().strftime("%Y-%m-%d")))
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
        if user[10] == 1: return {"error": "Вы забанены в NFTgram!"}
        
        return {"id": user[0], "nickname": user[1], "phone": user[2], "password": user[3], "stars": user[4], 
                "status": user[5], "created_at": user[7], "avatar": user[8], "role": user[9], 
                "username": user[11], "custom_id": user[12], "bio": user[13]}
    raise HTTPException(status_code=401, detail="Неверный Ник или Пароль")

@app.post("/api/upload_avatar")
async def upload_avatar(nickname: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    encoded_string = base64.b64encode(contents).decode('utf-8')
    base64_url = f"data:{file.content_type};base64,{encoded_string}"
    
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
    if data.get("new_username"): c.execute("UPDATE users SET username = ? WHERE nickname = ?", (data.get("new_username"), data.get("nickname")))
    if data.get("new_bio") is not None: c.execute("UPDATE users SET bio = ? WHERE nickname = ?", (data.get("new_bio"), data.get("nickname")))
    if data.get("new_pass"): c.execute("UPDATE users SET password = ? WHERE nickname = ?", (data.get("new_pass"), data.get("nickname")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/tops")
def get_tops():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    # ТЕПЕРЬ ЗДЕСЬ ВСЕ ДАННЫЕ ДЛЯ ПРОСМОТРА ПРОФИЛЯ
    c.execute("SELECT nickname, stars, avatar, username, custom_id, bio, role FROM users ORDER BY stars DESC LIMIT 10")
    users = c.fetchall()
    conn.close()
    return [{"nickname": u[0], "stars": u[1], "avatar": u[2], "username": u[3], "custom_id": u[4], "bio": u[5], "role": u[6]} for u in users]

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Spyke": raise HTTPException(status_code=403, detail="Неверный пароль админа!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    
    target_id = str(data.get("target_id"))
    value = data.get("value")
    
    if data.get("action") == "stars": 
        c.execute("UPDATE users SET stars = ? WHERE custom_id = ?", (int(value), target_id))
    elif data.get("action") == "role": 
        c.execute("UPDATE users SET role = ? WHERE custom_id = ?", (value, target_id))
    elif data.get("action") == "ban": 
        c.execute("UPDATE users SET is_banned = ? WHERE custom_id = ?", (int(value), target_id))
    
    conn.commit()
    conn.close()
    return {"status": "ok"}
