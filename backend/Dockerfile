# Usamos una versión ligera de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y fuerza a que la salida de consola sea en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los requerimientos y los instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código de nuestro proyecto
COPY . .

# Comando para arrancar el servidor de FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]