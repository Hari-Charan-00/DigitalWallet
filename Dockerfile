FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest

COPY . .

EXPOSE 9000

CMD ["uvicorn", "DigiApi:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
