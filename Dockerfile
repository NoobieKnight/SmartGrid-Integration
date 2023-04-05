FROM python:3.9-slim-buster

WORKDIR /src

COPY /src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY /src/main.py ./

ENTRYPOINT [ "python", "-u", "main.py" ]
EXPOSE 5000
