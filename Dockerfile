FROM python:3.8-slim-buster

WORKDIR /app

RUN pip3 install aiohttp python-dotenv discord.py

COPY . .

CMD [ "python3", "main.py" ]
