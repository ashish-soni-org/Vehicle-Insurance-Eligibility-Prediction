FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 5000

# CMD ["python3", "main.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
