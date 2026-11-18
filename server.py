from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import random

app = FastAPI()
users_db = {}
messages_db = []

class NameRequest(BaseModel):
    name: str

class MsgRequest(BaseModel):
    sender: str
    text: str

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>NFTgram - Вход</title>
    <style>
        body { background-color: #0e1621; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background-color: #17212b; padding: 40px; border-radius: 15px; text-align: center; width: 350px; }
        h1 { color: #64b5f6; }
        input { width: 90%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; background-color: #242f3d; color: white; }
        button { background-color: #64b5f6; color: #0e1621; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 15px; }
        button:hover { background-color: #42a5f5; }
        .result { margin-top: 20px; display: none; }
    </style>
</head>
<body>
<div class="container">
    <h1>NFTgram</h1>
    <p>Введите имя для получения номера</p>
    <div id="registerForm">
        <input type="text" id="nameInput" placeholder="Ваше имя">
        <button onclick="register()">Получить номер</button>
    </div>
    <div class="result" id="resultBox">
        <p>Ваш номер:</p>
        <h2 id="phoneDisplay" style="color: #64b5f6;"></h2>
        <p style="font-size: 14px; color: #a0a0a0;">Сохраните его для входа</p>
    </div>
</div>
<script>
    async function register() {
        const name = document.getElementById('nameInput').value;
        if (!name) return alert("Введите имя!");
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        const data = await response.json();
        if (data.status === 'ok') {
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('resultBox').style.display = 'block';
            document.getElementById('phoneDisplay').innerText = data.phone;
        }
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_PAGE

@app.post("/api/register")
def register_user(data: NameRequest):
    new_phone = f"+{random.randint(1000, 9999)}"
    while new_phone in users_db:
        new_phone = f"+{random.randint(1000, 9999)}"
    users_db[new_phone] = {
        "phone": new_phone, "name": data.name, "stars": 1000000,
        "status": "admin" if data.name.lower() == "admin" else "user", "gifts": []
    }
    return {"status": "ok", "phone": new_phone}

@app.get("/user/{phone}")
def get_user(phone: str):
    if phone not in users_db:
        raise HTTPException(status_code=404, detail="Не найден")
    return users_db[phone]

@app.post("/send_message")
def send_message(data: MsgRequest):
    messages_db.append({"sender": data.sender, "text": data.text})
    return {"status": "ok"}

@app.get("/get_messages")
def get_messages():
    return messages_db

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
