FROM python:3.10

WORKDIR /code

COPY ./api/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./api /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]