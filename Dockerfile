
FROM python:3.12-slim


WORKDIR /app


COPY ./bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./bot/ .


EXPOSE 5000


CMD ["python", "panirbot.py"]
