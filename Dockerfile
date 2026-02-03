# Usar uma imagem leve do Python
FROM python:3.12-slim

# Definir diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema necessárias para algumas bibliotecas Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de dependências primeiro (otimiza o cache do Docker)
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código para o container
COPY . .

# Criar um volume para persistência do banco de dados SQLite
VOLUME ["/app/data"]

# Ajustar o main.py ou a configuração para salvar o banco na pasta /app/data/ se desejado
# Por padrão, vamos manter na raiz para compatibilidade com o atual, 
# mas no docker-compose mapeamos o arquivo.

# Comando para iniciar o bot
CMD ["python", "main.py"]
