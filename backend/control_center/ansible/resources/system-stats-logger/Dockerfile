FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc python3-dev
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "monitor.py"]
