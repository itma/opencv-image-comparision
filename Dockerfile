FROM python:3
EXPOSE 5678

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python
RUN pip install imutils
RUN pip install pickle-mixin
RUN pip install scikit-image
RUN pip install opencv-contrib-python
RUN pip install debugpy
RUN pip install pandas
RUN pip install psycopg2
