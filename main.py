
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy import insert, select
from db import database, rutas
import pandas as pd
import io

app = FastAPI()

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar plantillas
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Página principal
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Modelo de datos
class Ubicacion(BaseModel):
    latitud: float
    longitud: float
    fecha_hora: str
    tipo: str
    cedula: str

# Guardar ubicación
@app.post("/guardar")
async def guardar_ubicacion(ubicacion: Ubicacion):
    query = insert(rutas).values(
        latitud=ubicacion.latitud,
        longitud=ubicacion.longitud,
        fecha_hora=(datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        tipo=ubicacion.tipo,
        cedula=ubicacion.cedula
    )
    await database.execute(query)
    return {"mensaje": "Ubicación guardada en base de datos"}

# Página del administrador
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Obtener rutas
@app.get("/rutas")
async def obtener_rutas():
    query = select(rutas)
    resultados = await database.fetch_all(query)
    return [dict(r) for r in resultados]

# Descargar rutas como CSV
@app.get("/descargar")
async def descargar_rutas():
    query = select(rutas)
    resultados = await database.fetch_all(query)
    df = pd.DataFrame(resultados)
    if df.empty:
        return JSONResponse(content={"error": "No hay datos para exportar."})

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type='text/csv', headers={
        "Content-Disposition": "attachment; filename=rutas.csv"
    })

# Página del dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Datos del dashboard
@app.get("/dashboard-data")
async def dashboard_data():
    query = select(rutas)
    resultados = await database.fetch_all(query)
    df = pd.DataFrame(resultados, columns=["latitud", "longitud", "fecha_hora", "tipo", "cedula"])

    if df.empty:
        return JSONResponse(content={})

    total_rutas = len(df)
    top_cedulas = df["cedula"].value_counts().head(5).to_dict()
    df['hora'] = pd.to_datetime(df['fecha_hora']).dt.hour
    horas_activas = df['hora'].value_counts().sort_index().to_dict()
    df['dia_semana'] = pd.to_datetime(df['fecha_hora']).dt.day_name()
    dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    frecuencia_dias = {dia: 0 for dia in dias}
    conteo_dias = df['dia_semana'].value_counts().to_dict()
    for dia in dias:
        if dia in conteo_dias:
            frecuencia_dias[dia] = conteo_dias[dia]

    return JSONResponse(content={
        "total_rutas": total_rutas,
        "top_cedulas": top_cedulas,
        "horas_activas": horas_activas,
        "frecuencia_dias": frecuencia_dias
    })

# Descargar resumen del dashboard
@app.get("/descargar-dashboard")
async def descargar_dashboard():
    query = select(rutas)
    resultados = await database.fetch_all(query)
    df = pd.DataFrame(resultados)
    resumen_df = pd.DataFrame({"total_rutas": [len(df)]})
    output = io.StringIO()
    resumen_df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=dashboard_resumen.csv"
    })
