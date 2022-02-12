FROM python:3.8

RUN pip install --upgrade pip

WORKDIR /home/app/web

COPY . .

RUN pip install -r requirements.txt

CMD gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
