FROM python:3.12 

WORKDIR /app

COPY main.py .
COPY requirements.txt .
COPY tables.sql .
COPY templates ./templates
COPY static ./static

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8000", "main:app"]
