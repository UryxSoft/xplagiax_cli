# Imagen base oficial de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar requirements y código
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expone el puerto usado por Flask
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]
