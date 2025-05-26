# syntax=docker/dockerfile:1

FROM python:3.9-slim

WORKDIR /lidar_to_acad_points

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN apt update
RUN apt install gdal-bin -y

COPY . .

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
#CMD ["python", "app.py"]