FROM python:3.12

RUN adduser --disabled-password --gecos '' --uid 1000 myuser

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chown -R myuser:myuser /app

USER myuser

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
