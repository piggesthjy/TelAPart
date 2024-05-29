FROM ubuntu:20.04

RUN apt update -y && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends python3 python3-dev python3-pip
RUN pip install --upgrade pip
RUN pip install scipy numpy scikit-learn networkx python-louvain

COPY ./main.py /
COPY ./data_preprocessing.py /
COPY ./issue_detector.py /

RUN cd /

ENTRYPOINT ["python3", "main.py"]
