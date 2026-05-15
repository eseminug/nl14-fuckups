FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_RUN_ON_SAVE=false

WORKDIR /app

# install build dependencies for some wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy application
COPY . /app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app

# run as non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8501

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
