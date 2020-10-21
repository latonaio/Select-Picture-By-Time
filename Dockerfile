FROM l4t:latest

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=select-picture-by-time \
    AION_HOME=/var/lib/aion

# Setup Directoties
RUN mkdir -p ${AION_HOME}/$POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

ADD requirements.txt .

RUN pip3 install --upgrade pip && \
    pip3 install -r ./requirements.txt

ADD main.py .

CMD ["python3", "-u", "main.py"]
