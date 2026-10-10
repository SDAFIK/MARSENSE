FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
COPY ai/requirements.txt ai/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && pip install --no-cache-dir -r ai/requirements.txt --index-url https://download.pytorch.org/whl/cpu
COPY backend backend
COPY ai ai
COPY data/nasa data/nasa
COPY data/processed data/processed
COPY data/demo data/demo
RUN useradd --create-home marsense && mkdir -p data/runtime && chown -R marsense:marsense /app
USER marsense
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
