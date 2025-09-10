FROM python:3.12-slim
RUN pip install uv

COPY config/requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]