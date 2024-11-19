FROM python:3.10-slim

RUN apt update
WORKDIR /src
COPY ./src/req.txt .

RUN pip install --upgrade pip
RUN pip install -r req.txt
COPY ./src /src


CMD ["python3","/src/tags_analysis.py"]