import asyncio
from dataclasses import dataclass
import random
import sys
import time
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from playwright.async_api import async_playwright
import threading
import threading
from typing import List, Dict
from pydantic import BaseModel
from pathlib import Path
import base64
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import asyncio
from dataclasses import dataclass
import random
import sys
import time
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from playwright.async_api import async_playwright
from typing import List, Dict, Optional
from pydantic import BaseModel
from pathlib import Path
import base64
import json
from datetime import datetime, timedelta
import logging


if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()


# Configura os templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory task storage (replace with a database for persistence)
tasks: List[Dict] = []

# Define global variables for WhatsApp connection status
whatsapp_connected = False
qr_code_image = None
connection_status_lock = threading.Lock()
page_lock = threading.Lock()
browser_page = None
connected_clients = []
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@dataclass
class ScheduledTask:
    id: int
    contact: str
    message: str
    scheduled_time: float
    retries: int = 0
    max_retries: int = 3
    retry_delay: int = 180  # 3 minutes

class Task(BaseModel):
    id: Optional[int]
    contact: str
    message: str
    scheduled_time: float


class TaskScheduler:
    def __init__(self):
        self.tasks: List[ScheduledTask] = []
        self.running = False
        self._task_lock = asyncio.Lock()  # Add lock for thread safety
    
    async def start(self):
        self.running = True
        while self.running:
            now = datetime.now().timestamp()
            async with self._task_lock:
                for task in self.tasks[:]:
                    if task.scheduled_time <= now:
                        asyncio.create_task(self._process_task(task))
                        self.tasks.remove(task)
            await asyncio.sleep(1)
    
    async def _process_task(self, task: ScheduledTask):
        success = await send_whatsapp_message(task.contact, task.message)
        if not success and task.retries < task.max_retries:
            task.retries += 1
            task.scheduled_time = (datetime.now() + timedelta(seconds=task.retry_delay)).timestamp()
            async with self._task_lock:
                self.tasks.append(task)
                self.tasks.sort(key=lambda x: x.scheduled_time)
            logging.info(f"Reagendando tarefa {task.id} para retry {task.retries}")
    
    async def add_task(self, task: ScheduledTask):
        async with self._task_lock:
            self.tasks.append(task)
            self.tasks.sort(key=lambda x: x.scheduled_time)
    
    async def remove_task(self, task_id: int) -> bool:
        async with self._task_lock:
            for task in self.tasks[:]:
                if task.id == task_id:
                    self.tasks.remove(task)
                    return True
            return False

scheduler = TaskScheduler()


async def main():
    global whatsapp_connected, qr_code_image, browser_page
    
    user_data_dir = Path("./browser_data")
    user_data_dir.mkdir(exist_ok=True)

    def human_delay():
        time.sleep(random.uniform(0.5, 3))  

    async with async_playwright() as p:
        try:
            user_agent = random.choice(user_agents)

            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials"
                ],
                viewport={"width": 1280, "height": 800},
                user_agent=user_agent,
                chromium_sandbox=False,
                bypass_csp=True,
                ignore_default_args=["--enable-automation"]
            )

            page = await browser.new_page()

            await page.goto("https://web.whatsapp.com")
            human_delay()

            print("Página carregada:", await page.title())
            browser_page = page

            await browser_page.wait_for_event("close" , timeout = 0)
            
        except Exception as e:
            print(f"Erro ao iniciar o navegador: {e}")

                
async def check_connection():
    global whatsapp_connected, qr_code_image, browser_page
    try:
        qr_element = await browser_page.query_selector('canvas')

        if await browser_page.query_selector('div:has-text("Clique para recarregar o QR code")'):
            print("QR Code expirado. Recarregando página...")
            await browser_page.reload()
            await asyncio.sleep(2)
        
        elif qr_element:
            whatsapp_connected = False
            screenshot = await qr_element.screenshot()
            img_base64 = base64.b64encode(screenshot).decode('utf-8')
            qr_code_image = f"data:image/png;base64,{img_base64}"
            print("QR code atualizado.")
            await notify_clients(json.dumps({
                "event": "qr_updated",
                "data": {
                    "connected": whatsapp_connected,
                    "qrCode": qr_code_image
                }
            }))

        # Verifica se conectou
        elif await browser_page.query_selector('button[aria-label="Nova conversa"][role="button"]'):
            whatsapp_connected = True
            qr_code_image = None
            print("WhatsApp Web conectado com sucesso.")
            await notify_clients(json.dumps({
                "event": "connection_status",
                "data": {
                    "connected": whatsapp_connected
                }
            }))

    except Exception as e:
        print(f"Erro na verificação de conexão: {e}")

async def send_whatsapp_message(contact: str, message: str) -> bool:
    """
    Send a WhatsApp message using Playwright.
    Returns True if successful, False otherwise.
    """
    global browser_page, whatsapp_connected
    
    try:
        if not whatsapp_connected or not browser_page:
            logging.error("WhatsApp não está conectado")
            return False

        # Click new chat button
        await browser_page.click('button[aria-label="Nova conversa"][role="button"]')
        
        # Wait and fill search input
        search_input = await browser_page.wait_for_selector('div[contenteditable="true"][data-tab="3"]')
        await search_input.fill(contact)
        await search_input.press('Enter')

        message_input = await browser_page.wait_for_selector('div[contenteditable="true"][data-tab="10"]')
        await message_input.fill(message)
        
        # Send message
        await browser_page.click('span[data-icon="send"]')
        
        logging.info(f"Mensagem enviada para {contact}: {message}")
        return True

    except Exception as e:
        logging.error(f"Erro ao enviar mensagem: {e}")
        return False

# Update startup event
@app.on_event("startup")
async def startup_event():
    asyncio.get_running_loop().create_task(main())
    await asyncio.sleep(5)
    asyncio.get_running_loop().create_task(background_checker())
    # Start the scheduler
    asyncio.get_running_loop().create_task(scheduler.start())

async def background_checker():
    while True:
        await check_connection()
        if whatsapp_connected: break

        await asyncio.sleep(5) 


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/whatsapp-status")
async def get_whatsapp_status():
    await check_connection()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print("WebSocket desconectado:", e)
    finally:
        connected_clients.remove(websocket)

async def notify_clients(message: str):
    for client in connected_clients:
        await client.send_text(message)

# --- API Endpoints for Task Management ---
@app.post("/zapAgenda/", response_model=Task)
async def create_task(task: Task):
    task_dict = task.dict()
    task_dict['id'] = len(tasks) + 1
    
    scheduled_task = ScheduledTask(
        id=task_dict['id'],
        contact=task.contact,
        message=task.message,
        scheduled_time=task.scheduled_time
    )
    
    await scheduler.add_task(scheduled_task)
    tasks.append(task_dict)
    return task

@app.get("/zapAgenda/", response_model=List[Task])
async def read_tasks():
    return tasks

@app.get("/zapAgenda/{task_id}", response_model=Task)
async def read_task(task_id: int):
    for task in tasks:
        if task['id'] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.put("/zapAgenda/{task_id}", response_model=Task)
async def update_task(task_id: int, updated_task: Task):
    for index, task in enumerate(tasks):
        if task['id'] == task_id:
            updated_task_dict = updated_task.dict()
            updated_task_dict['id'] = task_id
            tasks[index] = updated_task_dict
            return updated_task_dict
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/zapAgenda/{task_id}", status_code=204)
async def delete_task(task_id: int):
    if scheduler.remove_task(task_id):
        for index, task in enumerate(tasks):
            if task['id'] == task_id:
                del tasks[index]
                return
    raise HTTPException(status_code=404, detail="Task not found")

# Example usage in a route
@app.post("/test-message")
async def test_message(contact: str, message: str):
    success = await send_whatsapp_message(contact, message)
    if success:
        return {"status": "success", "message": "Mensagem enviada"}
    return {"status": "error", "message": "Falha ao enviar mensagem"}

@app.post("/tasks")
async def create_task(task: Task):
    task_id = len(scheduler.tasks) + 1
    scheduled_task = ScheduledTask(
        id=task_id,
        contact=task.contact,
        message=task.message,
        scheduled_time=task.scheduled_time
    )
    await scheduler.add_task(scheduled_task)
    return {"message": "Task scheduled successfully", "task_id": task_id}
