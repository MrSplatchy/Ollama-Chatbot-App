FROM python:3.12-slim

WORKDIR /server

COPY . /server/

RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 8000 

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
