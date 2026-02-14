LABEL org.opencontainers.image.authors="nurefexc"
LABEL org.opencontainers.image.source="https://github.com/nurefexc/radicale-ntfy-birthday-alert"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/nurefexc/radicale-ntfy-birthday-alert"
LABEL org.opencontainers.image.description="Radicale CardDAV birthday to ntfy.sh alert bridge"

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD ["python", "main.py"]
