FROM python:3.12

WORKDIR /python
COPY python/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY python/ .
RUN mkdir -p logs

CMD ["python", "main.py"]
