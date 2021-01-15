FROM python:3.7-alpine
WORKDIR /static_app

COPY ./main_app /static_app

RUN apk add --no-cache gcc musl-dev linux-headers openssl-dev libffi-dev
RUN pip install -r requirements.txt

CMD ["python", "app.py"]