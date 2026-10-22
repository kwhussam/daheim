ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY backend/app ./app
COPY frontend/wizard /frontend/wizard

COPY ha_addon/daheim_plus_agent/run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099

CMD [ "/run.sh" ]
