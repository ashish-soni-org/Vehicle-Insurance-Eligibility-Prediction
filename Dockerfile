FROM python:3.10-slim

WORKDIR /app
COPY ./ProductionFiles /app

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 5000

CMD ["python3", "app.py"]