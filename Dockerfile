# python:alpine is 3.{latest}
FROM python:2-stretch 

RUN pip install flask arrow  bs4  pypandoc

RUN apt-get update && apt-get --yes install pandoc

COPY . /src/

EXPOSE 5000

ENTRYPOINT ["python", "/src/app.py"]
