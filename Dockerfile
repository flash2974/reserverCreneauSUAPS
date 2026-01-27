FROM python:3.12-slim
RUN pip install uv

COPY config/requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 5000

HEALTHCHECK CMD python -c "import requests, sys; \
try: \
    r = requests.get('http://localhost:5000/health', timeout=5); \
    sys.exit(0 if r.status_code == 200 else 1); \
except: sys.exit(1)"

#CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "src.main:app"]
# CMD ["python", "-m", "src.main"]
CMD ["sh", "-c", "if [ \"$DEBUG\" = \"True\" ]; then python -m src.main; else gunicorn -w 1 --worker-class gthread --threads 4 --timeout 60 -b 0.0.0.0:5000 src.main:app; fi"]