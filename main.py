from fastapi import FastAPI, routing
from routers import notifications
app = FastAPI()

@app.get("/")
async def read_root():
    return {"Estado de la API": "Funcionando correctamente"}

app.include_router(notifications.router)