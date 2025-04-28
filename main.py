from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import csv
import os
import io

app = FastAPI()

# Montar los archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar las plantillas HTML
templates = Jinja2Templates(directory="templates")

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
    archivo = "rutas.csv"
    archivo_existe = os.path.isfile(archivo)

    # Ajustar la fecha y hora a UTC-5
    fecha_hora_utc5 = (datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")

    with open(archivo, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not archivo_existe:
            writer.writerow(["latitud", "longitud", "fecha_hora", "tipo", "cedula"])
        writer.writerow([ubicacion.latitud, ubicacion.longitud, fecha_hora_utc5, ubicacion.tipo, ubicacion.cedula])

    return {"mensaje": "Ubicación guardada correctamente"}

# Página del administrador
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Obtener rutas
@app.get("/rutas")
async def obtener_rutas():
    datos = []
    if os.path.exists("rutas.csv"):
        with open("rutas.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                datos.append({
                    "latitud": float(row["latitud"]),
                    "longitud": float(row["longitud"]),
                    "fecha_hora": row["fecha_hora"],
                    "tipo": row["tipo"],
                    "cedula": row["cedula"]
                })
    return datos

# Descargar rutas
@app.get("/descargar")
async def descargar_rutas():
    return FileResponse("rutas.csv", media_type='text/csv', filename="rutas.csv")

# Página dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Datos para el dashboard
@app.get("/dashboard-data")
async def dashboard_data():
    if not os.path.exists("rutas.csv"):
        return JSONResponse(content={})

    df = pd.read_csv("rutas.csv")

    total_rutas = len(df)

    top_cedulas = df["cedula"].value_counts().head(5).to_dict()

    df['hora'] = pd.to_datetime(df['fecha_hora']).dt.hour
    horas_activas = df['hora'].value_counts().sort_index().to_dict()

    # Frecuencia por día de la semana (lunes a domingo)
    df['dia_semana'] = pd.to_datetime(df['fecha_hora']).dt.day_name()
    dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    frecuencia_dias = {dia: 0 for dia in dias}

    conteo_dias = df['dia_semana'].value_counts().to_dict()
    for dia in dias:
        if dia in conteo_dias:
            frecuencia_dias[dia] = conteo_dias[dia]

    resumen = {
        "total_rutas": total_rutas,
        "top_cedulas": top_cedulas,
        "horas_activas": horas_activas,
        "frecuencia_dias": frecuencia_dias
    }

    return JSONResponse(content=resumen)

# Descargar resumen de dashboard
@app.get("/descargar-dashboard")
async def descargar_dashboard():
    if not os.path.exists("rutas.csv"):
        return {"error": "No existen datos."}

    df = pd.read_csv("rutas.csv")
    resumen = {
        "total_rutas": [len(df)]
    }
    resumen_df = pd.DataFrame(resumen)

    output = io.StringIO()
    resumen_df.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=dashboard_resumen.csv"})
