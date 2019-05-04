ARG ROOT

FROM ${ROOT}

ADD ./app_export /var/lib/deepomatic

ENV AUTOSTART_WORKER true
ENV DEEPOMATIC_STORAGE_DIR /var/lib/deepomatic/services/worker-nn
ENV WORKFLOWS_PATH /var/lib/deepomatic/services/worker-nn/resources/workflows.json
