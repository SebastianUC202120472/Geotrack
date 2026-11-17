FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Incluye la semilla de la base de conocimiento y el aviso de privacidad (app/conocimiento/*.json).
COPY app ./app

# El servicio corre sin privilegios de root.
RUN useradd --create-home --uid 10002 atencion
USER atencion

EXPOSE 8200
# Sin --proxy-headers: la IP del visitante se toma solo de X-Real-IP, que escribe Nginx.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
