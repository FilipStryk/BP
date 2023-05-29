FROM python:3.10

WORKDIR /usr/src/app

COPY aggregator/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY aggregator/ .

CMD [ "python", "./main.py" ]