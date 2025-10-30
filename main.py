from fastapi import FastAPI, routing

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Estado de la API": "Funcionando correctamente"}