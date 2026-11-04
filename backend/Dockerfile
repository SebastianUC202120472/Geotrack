FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Modo produccion: sin --reload (vigila archivos y reinicia; solo sirve en desarrollo).
# Procesos: uvicorn toma WEB_CONCURRENCY (por defecto 1). El arranque es seguro con
# varios procesos (candado en Postgres), pero el limitador de intentos es por proceso.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
