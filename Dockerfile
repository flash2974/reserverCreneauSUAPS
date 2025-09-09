FROM python:3.12-slim
RUN pip install --upgrade pip

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r config/requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
