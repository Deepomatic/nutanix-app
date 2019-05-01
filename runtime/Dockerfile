ARG BASE_IMAGE

FROM ${BASE_IMAGE}

# Add our custom function
COPY . /app/runtime
WORKDIR /app

RUN make -C runtime/proto

# Containers should NOT run as root as a good practice
# We mandate all runtime containers to run as user 10001
USER 10001

# Finally run Python function worker which pull and executes functions.

CMD ["python", "runtime/main.py"]
