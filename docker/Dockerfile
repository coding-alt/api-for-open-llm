FROM nvcr.io/nvidia/pytorch:22.12-py3

WORKDIR /workspace/
ENV PYTHONPATH /workspace/
COPY requirements.txt /workspace/
COPY . /workspace

RUN pip install --no-cache-dir -r /workspace/requirements.txt && \
    pip install bitsandbytes --upgrade -i https://mirror.baidu.com/pypi/simple \
