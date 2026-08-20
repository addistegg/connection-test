FROM python:3.12-slim

WORKDIR /app

COPY server.py .

EXPOSE 7213

CMD ["python", "-u", "server.py"]
