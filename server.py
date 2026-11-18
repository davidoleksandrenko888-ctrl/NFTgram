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
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nickname TEXT UNIQUE, phone TEXT, password TEXT,
                 stars INTEGER DEFAULT 1000, status TEXT DEFAULT 'user',
                 badge TEXT DEFAULT '', created_at TEXT, avatar TEXT DEFAULT '',
                 role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0,
                 username TEXT UNIQUE, custom_id TEXT UNIQUE, bio TEXT DEFAULT '',
                 is_premium INTEGER DEFAULT 0)''')
    
    # Сообщения
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 sender_id TEXT, receiver_id TEXT, text TEXT, created_at TEXT)''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    c.execute("DELETE FROM users WHERE nickname = 'Admin' AND custom_id = '0000000000'")
    conn.commit()
    conn.close()

init_db()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFTgram ❄️</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            background: #0e1621; color: white; font-family: 'Inter', sans-serif; 
            height: 100vh; overflow: hidden; display: flex; 
        }

        /* УВЕДОМЛЕНИЯ */
        #toast-container { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; flex-direction: column; gap: 10px; align-items: center; pointer-events: none; }
        .toast { background: #17212b; padding: 12px 24px; border-radius: 10px; font-weight: 500; border: 1px solid #242f3d; box-shadow: 0 5px 15px rgba(0,0,0,0.5); animation: popUp 0.3s; }
        @keyframes popUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* ЭКРАН АВТОРИЗАЦИИ */
        .auth-wrapper { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: #0e1621; z-index: 1000; }
        .auth-card { background: #17212b; padding: 40px; border-radius: 15px; width: 350px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .auth-card h1 { color: #64b5f6; text-align: center; margin-bottom: 20px; font-size: 26px; }
        .input-group { margin-bottom: 15px; }
        input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #242f3d; background: #242f3d; color: white; outline: none; font-size: 14px; }
        input:focus { border-color: #64b5f6; }
        .btn-primary { width: 100%; padding: 12px; border-radius: 8px; border: none; background: #64b5f6; color: #0e1621; font-weight: 700; cursor: pointer; font-size: 15px; margin-top: 10px; }
        .btn-primary:hover { background: #42a5f5; }
        .auth-link { display: block; text-align: center; color: #64b5f6; margin-top: 15px; cursor: pointer; font-size: 14px; }

        /* ОСНОВНОЙ ИНТЕРФЕЙС (КАК ТЕЛЕГРАМ) */
        #appScreen { display: none; width: 100%; height: 100%; flex-direction: row; }

        /* 1. ЛЕВАЯ ПАНЕЛЬ (ИКОНКИ) */
        .nav-rail { width: 70px; background: #17212b; display: flex; flex-direction: column; align-items: center; padding: 15px 0; border-right: 1px solid #242f3d; }
        .nav-icon { width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; margin-bottom: 10px; color: #8b9eb0; transition: 0.2s; }
        .nav-icon:hover, .nav-icon.active { background: #242f3d; color: #64b5f6; }
        .nav-icon svg { width: 24px; height: 24px; fill: currentColor; }
        .nav-bottom { margin-top: auto; }

        /* 2. СПИСОК ЧАТОВ */
        .chat-list-panel { width: 320px; background: #17212b; display: flex; flex-direction: column; border-right: 1px solid #242f3d; }
        .search-header { padding: 10px 15px; }
        .search-header input { background: #242f3d; border-radius: 20px; padding: 10px 15px; }
        .chats-container { flex: 1; overflow-y: auto; }
        .chat-item { display: flex; align-items: center; padding: 10px 15px; cursor: pointer; transition: 0.2s; }
        .chat-item:hover, .chat-item.active { background: #242f3d; }
        .chat-avatar { width: 50px; height: 50px; border-radius: 50%; background: #0e1621; display: flex; justify-content: center; align-items: center; font-size: 24px; margin-right: 12px; overflow: hidden; flex-shrink: 0; }
        .chat-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .chat-info { flex: 1; overflow: hidden; }
        .chat-name { font-weight: 600; font-size: 15px; color: white; }
        .chat-last-msg { font-size: 13px; color: #8b9eb0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 3px; }

        /* 3. ОКНО ЧАТА */
        .chat-window { flex: 1; display: flex; flex-direction: column; background: #0e1621; position: relative; }
        .chat-empty { flex: 1; display: flex; justify-content: center; align-items: center; color: #8b9eb0; font-size: 16px; background: #0e1621; }
        
        .chat-header { height: 60px; background: #17212b; border-bottom: 1px solid #242f3d; display: flex; align-items: center; padding: 0 20px; }
        .chat-header .chat-name { font-size: 16px; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg-bubble { max-width: 60%; padding: 10px 15px; border-radius: 12px; font-size: 14px; line-height: 1.4; position: relative; }
        .msg-mine { align-self: flex-end; background: #2b5278; border-bottom-right-radius: 4px; }
        .msg-theirs { align-self: flex-start; background: #182533; border-bottom-left-radius: 4px; }
        .msg-time { font-size: 10px; color: rgba(255,255,255,0.5); text-align: right; margin-top: 4px; }
        
        .chat-input { padding: 15px; background: #17212b; display: flex; gap: 10px; }
        .chat-input input { flex: 1; background: #242f3d; border-radius: 20px; padding: 12px 20px; }
        .chat-input button { width: 45px; height: 45px; border-radius: 50%; background: #64b5f6; border: none; cursor: pointer; display: flex; justify-content: center; align-items: center; }
        .chat-input button svg { fill: #0e1621; width: 20px; height: 20px; }

        /* 4. ПАНЕЛЬ НАСТРОЕК И ПРОФИЛЯ (СБОКУ) */
        .settings-panel { width: 0; background: #17212b; border-left: 1px solid #242f3d; transition: 0.3s; overflow: hidden; display: flex; flex-direction: column; }
        .settings-panel.open { width: 350px; }
        .settings-header { padding: 20px; border-bottom: 1px solid #242f3d; display: flex; justify-content: space-between; align-items: center; }
        .close-btn { cursor: pointer; color: #8b9eb0; font-size: 20px; }
        .settings-content { padding: 20px; overflow-y: auto; flex: 1; }
        .profile-card { text-align: center; margin-bottom: 30px; }
        .profile-card .chat-avatar { width: 100px; height: 100px; margin: 0 auto 15px; font-size: 40px; }
        .settings-section { background: #242f3d; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
        .settings-title { font-size: 13px; color: #64b5f6; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }

        /* 5. NFT И PREMIUM */
        .nft-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; padding: 20px; }
        .nft-item { background: #17212b; border-radius: 15px; padding: 15px; text-align: center; border: 1px solid #242f3d; transition: 0.2s; cursor: pointer; }
        .nft-item:hover { border-color: #64b5f6; transform: scale(1.05); }
        .nft-img { font-size: 50px; margin-bottom: 10px; }
        .premium-badge { background: linear-gradient(45deg, #ffd700, #ff8c00); color: black; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 800; margin-left: 5px; }

        /* АДМИНКА */
        .admin-section { border: 1px solid #e53935; background: rgba(229,57,53,0.1); border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
<div id="toast-container"></div>

<!-- АВТОРИЗАЦИЯ -->
<div class="auth-wrapper" id="authScreen">
    <div class="auth-card">
        <h1>❄️ NFTgram</h1>
        <div id="loginForm">
            <div class="input-group"><input type="text" id="loginNick" placeholder="Ник"></div>
            <div class="input-group"><input type="password" id="loginPass" placeholder="Пароль"></div>
            <button class="btn-primary" onclick="login()">Войти</button>
            <span class="auth-link" onclick="toggleAuth('register')">Создать аккаунт</span>
        </div>
        <div id="registerForm" style="display:none;">
            <div class="input-group"><input type="text" id="regNick" placeholder="Ник"></div>
            <div class="input-group"><input type="password" id="regPass" placeholder="Пароль"></div>
            <button class="btn-primary" onclick="register()">Зарегистрироваться</button>
            <span class="auth-link" onclick="toggleAuth('login')">Уже есть аккаунт? Войти</span>
        </div>
    </div>
</div>

<!-- ПРИЛОЖЕНИЕ -->
<div id="appScreen">
    
    <!-- ЛЕВАЯ ПАНЕЛЬ ИКОНОК -->
    <div class="nav-rail">
        <div class="nav-icon" onclick="switchTab('chats', this)">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
        </div>
        <div class="nav-icon" onclick="switchTab('nft', this)">
            <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div class="nav-icon" onclick="switchTab('premium', this)">
            <svg viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
        </div>
        <div class="nav-bottom">
            <div class="nav-icon" onclick="toggleSettings()">
                <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
            </div>
        </div>
    </div>

    <!-- СПИСОК ЧАТОВ -->
    <div class="chat-list-panel" id="chatListPanel">
        <div class="search-header">
            <input type="text" placeholder="Поиск" oninput="filterChats(this.value)">
        </div>
        <div class="chats-container" id="chatList"></div>
    </div>

    <!-- ОКНО ЧАТА -->
    <div class="chat-window" id="chatWindow">
        <div class="chat-empty" id="chatEmpty">Выберите чат, чтобы начать общение</div>
        
        <div id="activeChat" style="display:none; flex-direction:column; height:100%;">
            <div class="chat-header">
                <div class="chat-avatar" id="headerAvatar">👤</div>
                <div>
                    <div class="chat-name" id="headerName">Ник</div>
                </div>
            </div>
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input">
                <input type="text" id="msgInput" placeholder="Написать сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>

        <!-- NFT ВКЛАДКА -->
        <div id="nftTab" style="display:none; height:100%; overflow-y:auto;">
            <div style="padding: 20px; border-bottom: 1px solid #242f3d;">
                <h2 style="font-size: 20px;">Мои NFT Подарки</h2>
            </div>
            <div class="nft-grid">
                <div class="nft-item" onclick="showToast('Вы купили Джелли-Кота за 500 звезд!')"><div class="nft-img">🐱</div><p>Джелли-Кот</p><p style="color:#fbc02d; font-size:12px;">500 ⭐</p></div>
                <div class="nft-item" onclick="showToast('Вы купили Пеплу за 1500 звезд!')"><div class="nft-img">🐸</div><p>Пепла</p><p style="color:#fbc02d; font-size:12px;">1500 ⭐</p></div>
                <div class="nft-item" onclick="showToast('Вы купили Шапку Дурова за 3000 звезд!')"><div class="nft-img">🧢</div><p>Шапка Дурова</p><p style="color:#fbc02d; font-size:12px;">3000 ⭐</p></div>
                <div class="nft-item" onclick="showToast('Вы купили Сердце за 100 звезд!')"><div class="nft-img">❤️</div><p>Сердце</p><p style="color:#fbc02d; font-size:12px;">100 ⭐</p></div>
            </div>
        </div>

        <!-- PREMIUM ВКЛАДКА -->
        <div id="premiumTab" style="display:none; height:100%; overflow-y:auto; padding: 40px; text-align: center;">
            <div style="font-size: 60px; margin-bottom: 20px;">⭐</div>
            <h2 style="margin-bottom: 10px;">Telegram Premium (NFTgram)</h2>
            <p style="color: #8b9eb0; margin-bottom: 30px;">Получи эксклюзивные стикеры, уникальные реакции и значок Premium.</p>
            <button class="btn-primary" style="max-width: 300px; margin: 0 auto;" onclick="buyPremium()">Купить за 5000 ⭐</button>
        </div>
    </div>

    <!-- ПАНЕЛЬ НАСТРОЕК (ВЫЕЗЖАЕТ СПРАВА) -->
    <div class="settings-panel" id="settingsPanel">
        <div class="settings-header">
            <h3 style="font-size: 18px;">Профиль и Настройки</h3>
            <div class="close-btn" onclick="toggleSettings()">✖</div>
        </div>
        <div class="settings-content">
            <div class="profile-card">
                <div class="chat-avatar" id="myAvatar">👤</div>
                <h3 id="myName">Ник</h3>
                <p style="color: #64b5f6; margin: 5px 0;" id="myUsername">@user</p>
                <p style="color: #8b9eb0; font-size: 13px;" id="myId">ID: 0</p>
                <p style="color: #fbc02d; font-weight: 700; margin-top: 10px;" id="myStars">1000 ⭐</p>
            </div>

            <div class="settings-section">
                <div class="settings-title">Изменить данные</div>
                <div class="input-group"><input type="text" id="newName" placeholder="Новое Имя"></div>
                <div class="input-group"><input type="text" id="newUsername" placeholder="Юзернейм (без @)"></div>
                <div class="input-group"><input type="password" id="newPass" placeholder="Новый Пароль"></div>
                <button class="btn-primary" onclick="updateProfile()">Сохранить</button>
            </div>

            <div class="settings-section">
                <div class="settings-title">Аватар</div>
                <input type="file" id="avatarUpload" accept="image/*" onchange="uploadAvatar()" style="display:none;">
                <button class="btn-primary" style="background:#242f3d; color:white;" onclick="document.getElementById('avatarUpload').click()">Загрузить фото</button>
            </div>

            <div class="settings-section" id="adminSection" style="display:none;">
                <div class="settings-title" style="color:#e53935;">Админка</div>
                <div class="input-group"><input type="password" id="adminPass" placeholder="Пароль админа"></div>
                <button class="btn-primary" onclick="checkAdmin()">Активировать</button>
                
                <div id="adminPanel" style="display:none; margin-top: 15px;">
                    <div class="input-group"><input type="text" id="adminTarget" placeholder="ID пользователя"></div>
                    <div class="input-group"><input type="number" id="adminStars" placeholder="Звезды"></div>
                    <button class="btn-primary" onclick="adminAction('stars')">Выдать звезды</button>
                    <div class="input-group" style="margin-top:10px;"><select id="adminRole"><option value="owner">owner</option><option value="admin">admin</option><option value="moder">moder</option><option value="user">user</option></select></div>
                    <button class="btn-primary" onclick="adminAction('role')">Сменить роль</button>
                </div>
            </div>

            <button class="btn-primary" style="background:#e53935; color:white; margin-top: 20px;" onclick="logout()">Выйти из аккаунта</button>
        </div>
    </div>
</div>

<script>
    let currentUser = null;
    let currentChatUser = null;
    let chatInterval = null;
    let allUsers = [];

    function showToast(msg) {
        const c = document.getElementById('toast-container');
        const t = document.createElement('div');
        t.className = 'toast'; t.innerText = msg;
        c.appendChild(t);
        setTimeout(() => t.remove(), 3000);
    }

    function toggleAuth(form) {
        document.getElementById('loginForm').style.display = form === 'login' ? 'block' : 'none';
        document.getElementById('registerForm').style.display = form === 'register' ? 'block' : 'none';
    }

    window.onload = () => {
        const u = localStorage.getItem('nftgram_user');
        if(u) {
            currentUser = JSON.parse(u);
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            updateUI();
            loadChats();
        }
    };

    async function register() {
        const nick = document.getElementById('regNick').value;
        const pass = document.getElementById('regPass').value;
        if(!nick || !pass) return showToast("Заполните поля!");
        const res = await fetch('/api/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nickname: nick, password: pass}) });
        if(res.ok) { showToast("Успешно! Войдите."); toggleAuth('login'); } else { showToast("Ник занят"); }
    }

    async function login() {
        const nick = document.getElementById('loginNick').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nickname: nick, password: pass}) });
        if(res.ok) {
            currentUser = await res.json();
            if(currentUser.error) return showToast(currentUser.error);
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            updateUI(); loadChats();
        } else { showToast("Ошибка входа"); }
    }

    function logout() { localStorage.removeItem('nftgram_user'); location.reload(); }

    function updateUI() {
        document.getElementById('myName').innerText = currentUser.nickname;
        document.getElementById('myUsername').innerText = currentUser.username;
        document.getElementById('myId').innerText = `ID: ${currentUser.custom_id}`;
        document.getElementById('myStars').innerText = `${currentUser.stars} ⭐`;
        
        const av = currentUser.avatar ? `<img src="${currentUser.avatar}">` : "👤";
        document.getElementById('myAvatar').innerHTML = av;
    }

    function toggleSettings() {
        document.getElementById('settingsPanel').classList.toggle('open');
    }

    async function loadChats() {
        const res = await fetch('/api/users');
        if(res.ok) {
            allUsers = await res.json();
            renderChats(allUsers);
        }
    }

    function renderChats(users) {
        const c = document.getElementById('chatList');
        c.innerHTML = '';
        users.forEach(u => {
            if(u.custom_id === currentUser.custom_id) return;
            const av = u.avatar ? `<img src="${u.avatar}">` : "👤";
            const premium = u.is_premium ? `<span class="premium-badge">PREMIUM</span>` : '';
            c.innerHTML += `
                <div class="chat-item" onclick='openChat(${JSON.stringify(u)})'>
                    <div class="chat-avatar">${av}</div>
                    <div class="chat-info">
                        <div class="chat-name">${u.nickname} ${premium}</div>
                        <div class="chat-last-msg">${u.username}</div>
                    </div>
                </div>
            `;
        });
    }

    function filterChats(val) {
        const filtered = allUsers.filter(u => u.nickname.toLowerCase().includes(val.toLowerCase()));
        renderChats(filtered);
    }

    function openChat(user) {
        currentChatUser = user;
        document.getElementById('chatEmpty').style.display = 'none';
        document.getElementById('nftTab').style.display = 'none';
        document.getElementById('premiumTab').style.display = 'none';
        
        const ac = document.getElementById('activeChat');
        ac.style.display = 'flex';
        
        document.getElementById('headerName').innerText = user.nickname;
        document.getElementById('headerAvatar').innerHTML = user.avatar ? `<img src="${user.avatar}">` : "👤";
        
        loadMessages();
        if(chatInterval) clearInterval(chatInterval);
        chatInterval = setInterval(loadMessages, 2000);
    }

    async function loadMessages() {
        if(!currentChatUser) return;
        const res = await fetch(`/api/messages/${currentChatUser.custom_id}?my_id=${currentUser.custom_id}`);
        if(res.ok) {
            const msgs = await res.json();
            const c = document.getElementById('chatMessages');
            c.innerHTML = '';
            msgs.forEach(m => {
                const isMe = m.sender_id === currentUser.custom_id;
                const time = new Date(m.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
                c.innerHTML += `<div class="msg-bubble ${isMe ? 'msg-mine' : 'msg-theirs'}">${m.text}<div class="msg-time">${time}</div></div>`;
            });
            c.scrollTop = c.scrollHeight;
        }
    }

    async function sendMessage() {
        const inp = document.getElementById('msgInput');
        const txt = inp.value.trim();
        if(!txt || !currentChatUser) return;
        inp.value = '';
        await fetch('/api/send_message', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sender_id: currentUser.custom_id, receiver_id: currentChatUser.custom_id, text: txt})
        });
        loadMessages();
    }

    function switchTab(tab, el) {
        document.querySelectorAll('.nav-icon').forEach(i => i.classList.remove('active'));
        el.classList.add('active');
        
        document.getElementById('chatEmpty').style.display = 'none';
        document.getElementById('activeChat').style.display = 'none';
        document.getElementById('nftTab').style.display = 'none';
        document.getElementById('premiumTab').style.display = 'none';
        
        if(tab === 'chats') {
            if(currentChatUser) document.getElementById('activeChat').style.display = 'flex';
            else document.getElementById('chatEmpty').style.display = 'flex';
        }
        if(tab === 'nft') document.getElementById('nftTab').style.display = 'block';
        if(tab === 'premium') document.getElementById('premiumTab').style.display = 'block';
    }

    async function buyPremium() {
        if(currentUser.stars < 5000) return showToast("Недостаточно звезд!");
        const res = await fetch('/api/buy_premium', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({custom_id: currentUser.custom_id})
        });
        if(res.ok) {
            currentUser.stars -= 5000;
            currentUser.is_premium = 1;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            updateUI(); showToast("Вы купили Premium! 👑");
        }
    }

    async function updateProfile() {
        const nn = document.getElementById('newName').value;
        const nu = document.getElementById('newUsername').value;
        const np = document.getElementById('newPass').value;
        const res = await fetch('/api/update_profile', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: currentUser.nickname, new_name: nn, new_username: nu ? "@"+nu : null, new_pass: np})
        });
        if(res.ok) {
            if(nn) currentUser.nickname = nn;
            if(nu) currentUser.username = "@"+nu;
            if(np) currentUser.password = np;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            updateUI(); showToast("Сохранено!");
        }
    }

    async function uploadAvatar() {
        const file = document.getElementById('avatarUpload').files[0];
        if(!file) return;
        const fd = new FormData();
        fd.append("file", file);
        fd.append("nickname", currentUser.nickname);
        const res = await fetch('/api/upload_avatar', {method: 'POST', body: fd});
        if(res.ok) {
            const data = await res.json();
            currentUser.avatar = data.avatar_url;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            updateUI(); showToast("Аватар обновлен!");
        }
    }

    function checkAdmin() {
        if(document.getElementById('adminPass').value === 'Spyke') {
            document.getElementById('adminPanel').style.display = 'block';
            showToast("Админка активна!");
        } else showToast("Неверный пароль!");
    }

    async function adminAction(act) {
        const tid = document.getElementById('adminTarget').value;
        let val = act === 'stars' ? document.getElementById('adminStars').value : document.getElementById('adminRole').value;
        if(!tid || !val) return showToast("Заполните поля!");
        const res = await fetch('/api/admin_action', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: "Spyke", target_id: tid, action: act, value: val})
        });
        if(res.ok) { showToast("Выполнено!"); loadChats(); } else showToast("Ошибка ID!");
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
    random_username = f"@user{random.randint(1000, 9999)}"
    random_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    try:
        c.execute("INSERT INTO users (nickname, phone, password, username, custom_id, stars, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (data.get("nickname"), f"+7{random.randint(9000000000, 9999999999)}", data.get("password"), random_username, random_id, 1000, "user", datetime.now().strftime("%Y-%m-%d")))
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
        return {"id": user[0], "nickname": user[1], "phone": user[2], "password": user[3], "stars": user[4], 
                "status": user[5], "created_at": user[7], "avatar": user[8], "role": user[9], 
                "username": user[11], "custom_id": user[12], "bio": user[13], "is_premium": user[14] if len(user) > 14 else 0}
    raise HTTPException(status_code=401, detail="Неверный Ник или Пароль")

@app.get("/api/users")
def get_users():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT nickname, avatar, username, custom_id, is_premium FROM users")
    users = c.fetchall()
    conn.close()
    return [{"nickname": u[0], "avatar": u[1], "username": u[2], "custom_id": u[3], "is_premium": u[4]} for u in users]

@app.post("/api/send_message")
def send_message(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, receiver_id, text, created_at) VALUES (?, ?, ?, ?)",
              (data.get("sender_id"), data.get("receiver_id"), data.get("text"), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/messages/{receiver_id}")
def get_messages(receiver_id: str, my_id: str):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute('''SELECT sender_id, text, created_at FROM messages 
                 WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) 
                 ORDER BY id ASC''', (my_id, receiver_id, receiver_id, my_id))
    msgs = c.fetchall()
    conn.close()
    return [{"sender_id": m[0], "text": m[1], "created_at": m[2]} for m in msgs]

@app.post("/api/buy_premium")
def buy_premium(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("UPDATE users SET stars = stars - 5000, is_premium = 1 WHERE custom_id = ?", (data.get("custom_id"),))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/update_profile")
def update_profile(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    if data.get("new_name"): c.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (data.get("new_name"), data.get("nickname")))
    if data.get("new_username"): c.execute("UPDATE users SET username = ? WHERE nickname = ?", (data.get("new_username"), data.get("nickname")))
    if data.get("new_pass"): c.execute("UPDATE users SET password = ? WHERE nickname = ?", (data.get("new_pass"), data.get("nickname")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

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

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Spyke": raise HTTPException(status_code=403, detail="Неверный пароль!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    target_id = str(data.get("target_id"))
    value = data.get("value")
    if data.get("action") == "stars": c.execute("UPDATE users SET stars = ? WHERE custom_id = ?", (int(value), target_id))
    elif data.get("action") == "role": c.execute("UPDATE users SET role = ? WHERE custom_id = ?", (value, target_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}
