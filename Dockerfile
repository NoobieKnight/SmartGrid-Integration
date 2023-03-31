FROM python:3.9-slim-buster

WORKDIR /src

COPY /src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "-m" ]
EXPOSE 5000