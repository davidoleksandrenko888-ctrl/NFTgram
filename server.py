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
                 stars INTEGER DEFAULT 1500, created_at TEXT, avatar TEXT DEFAULT '',
                 username TEXT UNIQUE, custom_id TEXT UNIQUE, bio TEXT DEFAULT '',
                 is_premium INTEGER DEFAULT 0, role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0)''')
    
    # Сообщения
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 sender_id TEXT, receiver_id TEXT, text TEXT, created_at TEXT)''')
    
    # Подарки (NFT)
    c.execute('''CREATE TABLE IF NOT EXISTS user_gifts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id TEXT, gift_name TEXT, gift_img TEXT, rarity TEXT)''')
    
    # Создаем официальные аккаунты
    bots = [
        ("Telegram", "+1 555 0100", "123", "@telegram", "7777777777", "Официальный аккаунт", "admin"),
        ("Saved Messages", "+1 555 0101", "123", "@saved", "0000000001", "Ваши сохраненные сообщения", "user"),
        ("Stickers", "+1 555 0102", "123", "@stickers", "8888888888", "Официальные стикеры", "admin"),
        ("NFT Store", "+1 555 0103", "123", "@nftstore", "9999999999", "Магазин подарков", "admin")
    ]
    
    for b in bots:
        c.execute("SELECT * FROM users WHERE custom_id = ?", (b[4],))
        if not c.fetchone():
            c.execute("INSERT INTO users (nickname, phone, password, username, custom_id, bio, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (b[0], b[1], b[2], b[3], b[4], b[5], b[6], datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

init_db()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFTgram</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        
        :root {
            --bg-color: #ffffff; --sidebar-bg: #ffffff; --chat-bg: #e6ebee;
            --text-color: #000000; --text-secondary: #707579; --border-color: #e1e1e1;
            --primary-color: #3390ec; --msg-mine: #eeffde; --msg-theirs: #ffffff; --hover-color: #f4f4f5;
        }

        body.dark-mode {
            --bg-color: #212121; --sidebar-bg: #212121; --chat-bg: #0f0f0f;
            --text-color: #ffffff; --text-secondary: #aaaaaa; --border-color: #333333;
            --msg-mine: #2b5278; --msg-theirs: #182533; --hover-color: #2c2c2c;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Roboto', sans-serif; }
        body { background: var(--bg-color); color: var(--text-color); height: 100vh; overflow: hidden; display: flex; }

        #toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; }
        .toast { background: var(--primary-color); color: white; padding: 12px 24px; border-radius: 10px; margin-bottom: 10px; animation: slideIn 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

        /* АВТОРИЗАЦИЯ */
        .auth-wrapper { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: var(--chat-bg); z-index: 1000; }
        .auth-card { background: var(--sidebar-bg); padding: 40px; border-radius: 15px; width: 380px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .auth-card h1 { color: var(--primary-color); text-align: center; margin-bottom: 20px; }
        .input-group { margin-bottom: 15px; }
        input, select, textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-color); color: var(--text-color); outline: none; }
        .btn { width: 100%; padding: 12px; border-radius: 8px; border: none; background: var(--primary-color); color: white; font-weight: 500; cursor: pointer; margin-top: 10px; transition: 0.2s;}
        .btn:hover { opacity: 0.9; }

        /* ОСНОВНОЙ ИНТЕРФЕЙС */
        #appScreen { display: none; width: 100%; height: 100%; flex-direction: row; }

        .nav-rail { width: 70px; background: var(--sidebar-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; align-items: center; padding: 15px 0; z-index: 10;}
        .nav-icon { width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center; cursor: pointer; margin-bottom: 10px; color: var(--text-secondary); transition: 0.2s; }
        .nav-icon:hover, .nav-icon.active { background: var(--hover-color); color: var(--primary-color); }
        .nav-icon svg { width: 24px; height: 24px; fill: currentColor; }
        .nav-bottom { margin-top: auto; }

        .chat-list-panel { width: 380px; background: var(--sidebar-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; }
        .search-header { padding: 10px 15px; display: flex; align-items: center; gap: 10px; }
        .search-header input { background: var(--hover-color); border-radius: 20px; border: none; padding: 10px 15px; }
        .chats-container { flex: 1; overflow-y: auto; }
        .chat-item { display: flex; padding: 10px 15px; cursor: pointer; transition: 0.1s; margin: 0 10px; border-radius: 10px; }
        .chat-item:hover { background: var(--hover-color); }
        .chat-item.active { background: var(--primary-color); color: white; }
        .chat-item.active .chat-last, .chat-item.active .chat-time { color: rgba(255,255,255,0.8); }
        .chat-avatar { width: 55px; height: 55px; border-radius: 50%; background: var(--border-color); display: flex; justify-content: center; align-items: center; font-size: 24px; color: var(--text-secondary); margin-right: 12px; overflow: hidden; flex-shrink: 0; }
        .chat-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .chat-info { flex: 1; overflow: hidden; }
        .chat-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; }
        .chat-name { font-weight: 500; font-size: 15px; display: flex; align-items: center; gap: 5px;}
        .chat-time { font-size: 12px; color: var(--text-secondary); }
        .chat-last { font-size: 14px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .chat-area { flex: 1; display: flex; flex-direction: column; background: var(--chat-bg) url('https://web.telegram.org/a/chat-bg-pattern-light.png'); background-size: cover; position: relative; }
        body.dark-mode .chat-area { background-image: url('https://web.telegram.org/a/chat-bg-pattern-dark.png'); }
        .chat-area.empty { justify-content: center; align-items: center; color: var(--text-secondary); }
        
        .chat-header { height: 60px; background: var(--sidebar-bg); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; padding: 0 20px; cursor: pointer; justify-content: space-between; }
        .chat-header-left { display: flex; align-items: center; }
        .chat-header .chat-avatar { width: 40px; height: 40px; font-size: 18px; }
        .header-info .name { font-weight: 500; font-size: 16px; }
        .header-info .status { font-size: 13px; color: var(--primary-color); }
        
        .messages { flex: 1; padding: 20px 5%; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
        .msg { max-width: 60%; padding: 8px 12px; border-radius: 12px; font-size: 14px; line-height: 1.4; box-shadow: 0 1px 2px rgba(0,0,0,0.1); color: var(--text-color); position: relative; }
        .msg.mine { align-self: flex-end; background: var(--msg-mine); border-bottom-right-radius: 4px; }
        .msg.theirs { align-self: flex-start; background: var(--msg-theirs); border-bottom-left-radius: 4px; }
        .msg-time { font-size: 11px; color: var(--text-secondary); float: right; margin: 5px 0 0 10px; }

        .input-area { padding: 10px 5%; background: var(--sidebar-bg); display: flex; align-items: center; gap: 10px; border-top: 1px solid var(--border-color); }
        .input-area input { flex: 1; background: var(--hover-color); border-radius: 20px; padding: 12px 20px; border: none; color: var(--text-color); }
        .input-area button { background: var(--primary-color); border: none; color: white; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; }

        /* МОДАЛКИ */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 200; justify-content: center; align-items: center; }
        .modal-content { background: var(--sidebar-bg); width: 450px; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto; position: relative;}
        .close-modal { position: absolute; top: 15px; right: 15px; cursor: pointer; font-size: 20px; color: var(--text-secondary); }

        /* NFT МАГАЗИН */
        .nft-store { display: none; flex: 1; background: var(--bg-color); overflow-y: auto; padding: 20px; }
        .nft-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .nft-item { background: var(--hover-color); border-radius: 15px; padding: 15px; text-align: center; cursor: pointer; transition: 0.2s; position: relative; }
        .nft-item:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .nft-img { font-size: 50px; margin-bottom: 10px; }
        .nft-rarity { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.6); color: white; font-size: 12px; padding: 2px 8px; border-radius: 10px; }
        .nft-price { color: var(--primary-color); font-weight: bold; margin-top: 5px; }

        .hidden { display: none !important; }
        .premium-badge { background: linear-gradient(45deg, #ffd700, #ff8c00); color: #000; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 800; margin-left: 5px; }
    </style>
</head>
<body>

<!-- АВТОРИЗАЦИЯ -->
<div class="auth-wrapper" id="authScreen">
    <div class="auth-card">
        <h1>NFTgram</h1>
        <div id="loginForm">
            <div class="input-group"><input type="text" id="loginNick" placeholder="Ник"></div>
            <div class="input-group"><input type="password" id="loginPass" placeholder="Пароль"></div>
            <button class="btn" onclick="login()">Войти</button>
            <div style="text-align:center; margin-top:15px; color:var(--primary-color); cursor:pointer;" onclick="toggleAuth('register')">Создать аккаунт</div>
        </div>
        <div id="registerForm" class="hidden">
            <div class="input-group"><input type="text" id="regNick" placeholder="Имя (Ник)"></div>
            <div class="input-group"><input type="password" id="regPass" placeholder="Пароль"></div>
            <p style="font-size:12px; color:var(--text-secondary); text-align:center;">Номер телефона сгенерируется автоматически</p>
            <button class="btn" onclick="register()">Зарегистрироваться</button>
            <div style="text-align:center; margin-top:15px; color:var(--primary-color); cursor:pointer;" onclick="toggleAuth('login')">Уже есть аккаунт? Войти</div>
        </div>
    </div>
</div>

<!-- ПРИЛОЖЕНИЕ -->
<div id="appScreen">
    
    <!-- ЛЕВАЯ ПАНЕЛЬ -->
    <div class="nav-rail">
        <div class="nav-icon active" onclick="switchTab('chats', this)">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
        </div>
        <div class="nav-icon" onclick="switchTab('nft', this)">
            <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div class="nav-bottom">
            <div class="nav-icon" onclick="openModal('settingsModal')">
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
    <div class="chat-area empty" id="chatArea">
        <div id="emptyState">Выберите чат</div>
        
        <div id="activeChat" class="hidden" style="height:100%; display:flex; flex-direction:column;">
            <div class="chat-header">
                <div class="chat-header-left">
                    <div class="chat-avatar" id="headerAvatar">👤</div>
                    <div class="header-info">
                        <div class="name" id="headerName">Имя</div>
                        <div class="status">в сети</div>
                    </div>
                </div>
            </div>
            <div class="messages" id="messagesContainer"></div>
            <div class="input-area">
                <input type="text" id="msgInput" placeholder="Написать сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">➤</button>
            </div>
        </div>

        <!-- МАГАЗИН NFT -->
        <div class="nft-store" id="nftStore">
            <h2>NFT Подарки</h2>
            <p style="color: var(--text-secondary); margin-top:5px;">Купи эксклюзивные подарки, они появятся у тебя в профиле.</p>
            <div class="nft-grid">
                <!-- Обычные -->
                <div class="nft-item" onclick="buyGift('❤️ Сердце', '❤️', '#111', 100)"><div class="nft-rarity">#111</div><div class="nft-img">❤️</div><div style="font-weight:500;">Сердце</div><div class="nft-price">100 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🎁 Подарок', '🎁', '#100', 250)"><div class="nft-rarity">#100</div><div class="nft-img">🎁</div><div style="font-weight:500;">Подарок</div><div class="nft-price">250 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🧸 Мишка', '🧸', '#102', 500)"><div class="nft-rarity">#102</div><div class="nft-img">🧸</div><div style="font-weight:500;">Мишка</div><div class="nft-price">500 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🍺 Пиво', '🍺', '#115', 400)"><div class="nft-rarity">#115</div><div class="nft-img">🍺</div><div style="font-weight:500;">Пиво</div><div class="nft-price">400 ⭐</div></div>
                <!-- Редкие -->
                <div class="nft-item" onclick="buyGift('🐸 Пепла', '🐸', '#142', 1500)"><div class="nft-rarity">#142</div><div class="nft-img">🐸</div><div style="font-weight:500;">Пепла</div><div class="nft-price">1500 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🍑 Персик', '🍑', '#140', 1200)"><div class="nft-rarity">#140</div><div class="nft-img">🍑</div><div style="font-weight:500;">Персик</div><div class="nft-price">1200 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('⚽ Мяч', '⚽', '#123', 800)"><div class="nft-rarity">#123</div><div class="nft-img">⚽</div><div style="font-weight:500;">Мяч</div><div class="nft-price">800 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🚀 Ракета', '🚀', '#131', 2500)"><div class="nft-rarity">#131</div><div class="nft-img">🚀</div><div style="font-weight:500;">Ракета</div><div class="nft-price">2500 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🎸 Гитара', '🎸', '#120', 1800)"><div class="nft-rarity">#120</div><div class="nft-img">🎸</div><div style="font-weight:500;">Гитара</div><div class="nft-price">1800 ⭐</div></div>
                <!-- Эпические -->
                <div class="nft-item" onclick="buyGift('🧢 Шапка Дурова', '🧢', '#103', 5000)"><div class="nft-rarity">#103</div><div class="nft-img">🧢</div><div style="font-weight:500;">Шапка Дурова</div><div class="nft-price">5000 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('🦄 Единорог', '🦄', '#199', 7500)"><div class="nft-rarity">#199</div><div class="nft-img">🦄</div><div style="font-weight:500;">Единорог</div><div class="nft-price">7500 ⭐</div></div>
                <div class="nft-item" onclick="buyGift('👑 Корона', '👑', '#001', 10000)"><div class="nft-rarity">#001</div><div class="nft-img">👑</div><div style="font-weight:500;">Корона</div><div class="nft-price">10000 ⭐</div></div>
            </div>
        </div>
    </div>

    <!-- МОДАЛКА НАСТРОЕК -->
    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="close-modal" onclick="closeModal('settingsModal')">✖</div>
            <h2 style="margin-bottom: 20px;">Настройки</h2>
            
            <div class="input-group"><label>Имя</label><input type="text" id="setName" placeholder="Новое Имя"></div>
            <div class="input-group"><label>Юзернейм</label><input type="text" id="setUser" placeholder="Новый Юзернейм (@)"></div>
            <div class="input-group"><label>Пароль</label><input type="password" id="setPass" placeholder="Новый Пароль"></div>
            <button class="btn" onclick="saveSettings()">Сохранить профиль</button>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid var(--border-color);">
            
            <button class="btn" style="background: #333;" onclick="toggleTheme()">Сменить тему</button>
            <button class="btn" style="background: #e53935; margin-top: 10px;" onclick="logout()">Выйти из аккаунта</button>
            
            <!-- СЕКРЕТНАЯ АДМИНКА -->
            <div style="margin-top: 30px; padding: 15px; border: 1px solid #e53935; border-radius: 10px;">
                <h4 style="color: #e53935; margin-bottom: 10px;">Админка (Пароль: Spyke)</h4>
                <div class="input-group"><input type="password" id="adminPass" placeholder="Пароль админа"></div>
                <button class="btn" style="background: #e53935;" onclick="checkAdmin()">Активировать</button>
                
                <div id="adminPanel" class="hidden" style="margin-top: 15px;">
                    <p style="font-size:12px; margin-bottom:5px; color:#e53935;">ID Пользователя:</p>
                    <div class="input-group"><input type="text" id="admTarget" placeholder="ID пользователя"></div>
                    
                    <p style="font-size:12px; margin-bottom:5px; color:#e53935;">Выдать звезды:</p>
                    <div class="input-group"><input type="number" id="admStars" placeholder="Кол-во"></div>
                    <button class="btn" onclick="admAction('stars')">Выдать</button>
                    
                    <p style="font-size:12px; margin-top:15px; margin-bottom:5px; color:#e53935;">Сменить роль:</p>
                    <div class="input-group">
                        <select id="admRole">
                            <option value="owner">owner</option>
                            <option value="admin">admin</option>
                            <option value="moder">moder</option>
                            <option value="user">user</option>
                            <option value="scam">scam</option>
                        </select>
                    </div>
                    <button class="btn" onclick="admAction('role')">Сменить роль</button>

                    <div style="display:flex; gap:10px; margin-top:15px;">
                        <button class="btn" style="background:#e53935;" onclick="admAction('ban')">Забанить</button>
                        <button class="btn" style="background:#43a047;" onclick="admAction('unban')">Разбанить</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

</div>

<script>
    let currentUser = null;
    let currentChatUser = null;
    let allUsers = [];
    let chatInterval = null;

    window.onload = () => {
        const u = localStorage.getItem('nftgram_user');
        if(u) {
            currentUser = JSON.parse(u);
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            loadChats();
        }
    };

    function toggleAuth(form) {
        document.getElementById('loginForm').classList.toggle('hidden', form !== 'login');
        document.getElementById('registerForm').classList.toggle('hidden', form !== 'register');
    }

    async function register() {
        const nick = document.getElementById('regNick').value;
        const pass = document.getElementById('regPass').value;
        if(!nick || !pass) return alert("Заполните поля!");
        const res = await fetch('/api/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nickname: nick, password: pass}) });
        if(res.ok) { alert("Успешно! Теперь войдите."); toggleAuth('login'); } else { alert("Ник занят"); }
    }

    async function login() {
        const nick = document.getElementById('loginNick').value;
        const pass = document.getElementById('loginPass').value;
        const res = await fetch('/api/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nickname: nick, password: pass}) });
        if(res.ok) {
            const data = await res.json();
            if(data.error) return alert(data.error);
            currentUser = data;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            document.getElementById('authScreen').style.display = 'none';
            document.getElementById('appScreen').style.display = 'flex';
            loadChats();
        } else { alert("Ошибка входа"); }
    }

    function switchTab(tab, el) {
        document.querySelectorAll('.nav-icon').forEach(i => i.classList.remove('active'));
        el.classList.add('active');
        
        document.getElementById('chatArea').classList.add('empty');
        document.getElementById('activeChat').classList.add('hidden');
        document.getElementById('nftStore').style.display = 'none';
        document.getElementById('emptyState').classList.remove('hidden');
        
        if(tab === 'chats') {
            document.getElementById('chatListPanel').style.display = 'flex';
            if(currentChatUser) {
                document.getElementById('chatArea').classList.remove('empty');
                document.getElementById('activeChat').classList.remove('hidden');
                document.getElementById('emptyState').classList.add('hidden');
            }
        }
        if(tab === 'nft') {
            document.getElementById('chatListPanel').style.display = 'none';
            document.getElementById('nftStore').style.display = 'block';
        }
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
            // Показываем всех, кроме себя (если это не Избранное)
            if(u.custom_id === currentUser.custom_id && u.nickname !== 'Saved Messages') return;
            
            const av = u.avatar ? `<img src="${u.avatar}">` : (u.nickname === 'Saved Messages' ? '🔖' : "👤");
            const activeClass = currentChatUser && currentChatUser.custom_id === u.custom_id ? 'active' : '';
            const isSaved = u.nickname === 'Saved Messages';
            
            c.innerHTML += `
                <div class="chat-item ${activeClass}" onclick='openChat(${JSON.stringify(u)})' id="chat-${u.custom_id}">
                    <div class="chat-avatar">${av}</div>
                    <div class="chat-info">
                        <div class="chat-top">
                            <div class="chat-name">${isSaved ? 'Избранное' : u.nickname}</div>
                            <div class="chat-time">12:30</div>
                        </div>
                        <div class="chat-last">${isSaved ? 'Сохранить сообщение...' : u.username}</div>
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
        document.getElementById('chatArea').classList.remove('empty');
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('activeChat').classList.remove('hidden');
        
        document.getElementById('headerName').innerText = user.nickname === 'Saved Messages' ? 'Избранное' : user.nickname;
        document.getElementById('headerAvatar').innerHTML = user.avatar ? `<img src="${user.avatar}">` : (user.nickname === 'Saved Messages' ? '🔖' : "👤");
        
        document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
        const el = document.getElementById('chat-' + user.custom_id);
        if(el) el.classList.add('active');

        loadMessages();
        if(chatInterval) clearInterval(chatInterval);
        chatInterval = setInterval(loadMessages, 2000);
    }

    async function loadMessages() {
        if(!currentChatUser) return;
        const res = await fetch(`/api/messages/${currentChatUser.custom_id}?my_id=${currentUser.custom_id}`);
        if(res.ok) {
            const msgs = await res.json();
            const c = document.getElementById('messagesContainer');
            c.innerHTML = '';
            msgs.forEach(m => {
                const isMe = m.sender_id === currentUser.custom_id;
                const time = new Date(m.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
                c.innerHTML += `<div class="msg ${isMe ? 'mine' : 'theirs'}">${m.text}<div class="msg-time">${time} ${isMe ? '✓✓' : ''}</div></div>`;
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

    // МАГАЗИН NFT
    async function buyGift(name, img, rarity, price) {
        if(currentUser.stars < price) return alert("Недостаточно звезд! Зайди в настройки -> Админка и выдай себе звезды.");
        const res = await fetch('/api/buy_gift', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: currentUser.custom_id, gift_name: name, gift_img: img, rarity: rarity, price: price})
        });
        if(res.ok) {
            currentUser.stars -= price;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            alert(`Вы успешно купили ${name}!`);
        }
    }

    // НАСТРОЙКИ И АДМИНКА
    function openModal(id) { document.getElementById(id).style.display = 'flex'; }
    function closeModal(id) { document.getElementById(id).style.display = 'none'; }
    function toggleTheme() { document.body.classList.toggle('dark-mode'); }
    function logout() { localStorage.removeItem('nftgram_user'); location.reload(); }

    async function saveSettings() {
        const nn = document.getElementById('setName').value;
        const nu = document.getElementById('setUser').value;
        const np = document.getElementById('setPass').value;
        const res = await fetch('/api/update_profile', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname: currentUser.nickname, new_name: nn, new_username: nu ? "@"+nu : null, new_pass: np})
        });
        if(res.ok) {
            if(nn) currentUser.nickname = nn;
            if(nu) currentUser.username = "@"+nu;
            if(np) currentUser.password = np;
            localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            alert("Сохранено!"); loadChats(); closeModal('settingsModal');
        }
    }

    function checkAdmin() {
        if(document.getElementById('adminPass').value === 'Spyke') {
            document.getElementById('adminPanel').classList.remove('hidden');
        } else alert("Неверный пароль!");
    }

    async function admAction(type) {
        const tid = document.getElementById('admTarget').value;
        if(!tid) return alert("Введите ID!");
        
        let val = "";
        if(type === 'stars') val = document.getElementById('admStars').value;
        if(type === 'role') val = document.getElementById('admRole').value;

        const res = await fetch('/api/admin_action', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({admin_pass: "Spyke", target_id: tid, action: type, value: val})
        });
        
        if(res.ok) { 
            alert("Выполнено!"); 
            if(tid === currentUser.custom_id && type === 'stars') {
                currentUser.stars += parseInt(val);
                localStorage.setItem('nftgram_user', JSON.stringify(currentUser));
            }
        } else alert("Ошибка! Проверьте ID.");
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
    # Рандомный номер
    random_phone = f"+7 {random.randint(900, 999)} {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
    
    try:
        c.execute("INSERT INTO users (nickname, phone, password, username, custom_id, stars, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (data.get("nickname"), random_phone, data.get("password"), random_username, random_id, 1500, datetime.now().strftime("%Y-%m-%d")))
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
        if user[11] == 1: return {"error": "Вы забанены!"}
        return {"id": user[0], "nickname": user[1], "phone": user[2], "password": user[3], "stars": user[4], 
                "created_at": user[5], "avatar": user[6], "username": user[7], "custom_id": user[8], "bio": user[9]}
    raise HTTPException(status_code=401, detail="Неверный Ник или Пароль")

@app.get("/api/users")
def get_users():
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("SELECT nickname, avatar, username, custom_id, bio, phone, is_premium FROM users WHERE is_banned = 0")
    users = c.fetchall()
    conn.close()
    return [{"nickname": u[0], "avatar": u[1], "username": u[2], "custom_id": u[3], "bio": u[4], "phone": u[5], "is_premium": u[6]} for u in users]

@app.post("/api/send_message")
def send_message(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    sender = data.get("sender_id")
    receiver = data.get("receiver_id")
    text = data.get("text")
    
    c.execute("INSERT INTO messages (sender_id, receiver_id, text, created_at) VALUES (?, ?, ?, ?)",
              (sender, receiver, text, datetime.now().isoformat()))
    
    # ЛОГИКА БОТОВ
    if receiver == "8888888888": # Sticker Bot
        reply = "Привет! Я официальный бот NFTgram. Вот тебе стикер: 🐸🔥"
        c.execute("INSERT INTO messages (sender_id, receiver_id, text, created_at) VALUES (?, ?, ?, ?)",
                  (receiver, sender, reply, datetime.now().isoformat()))
    elif receiver == "7777777777": # Telegram Bot
        reply = "Это тестовый аккаунт. Чтобы получить звезды, зайди в Настройки (шестеренка) и введи пароль Spyke."
        c.execute("INSERT INTO messages (sender_id, receiver_id, text, created_at) VALUES (?, ?, ?, ?)",
                  (receiver, sender, reply, datetime.now().isoformat()))
                  
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

@app.post("/api/buy_gift")
def buy_gift(data: dict):
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    c.execute("UPDATE users SET stars = stars - ? WHERE custom_id = ?", (data.get("price"), data.get("user_id")))
    c.execute("INSERT INTO user_gifts (user_id, gift_name, gift_img, rarity) VALUES (?, ?, ?, ?)",
              (data.get("user_id"), data.get("gift_name"), data.get("gift_img"), data.get("rarity")))
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

@app.post("/api/admin_action")
def admin_action(data: dict):
    if data.get("admin_pass") != "Spyke": raise HTTPException(status_code=403, detail="Неверный пароль!")
    conn = sqlite3.connect('nftgram.db')
    c = conn.cursor()
    target_id = str(data.get("target_id"))
    value = data.get("value")
    
    if data.get("action") == "stars": c.execute("UPDATE users SET stars = stars + ? WHERE custom_id = ?", (int(value), target_id))
    elif data.get("action") == "role": c.execute("UPDATE users SET role = ? WHERE custom_id = ?", (value, target_id))
    elif data.get("action") == "ban": c.execute("UPDATE users SET is_banned = 1 WHERE custom_id = ?", (target_id,))
    elif data.get("action") == "unban": c.execute("UPDATE users SET is_banned = 0 WHERE custom_id = ?", (target_id,))
    
    conn.commit()
    conn.close()
    return {"status": "ok"}
