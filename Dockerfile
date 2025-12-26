FROM python:3.10-slim

WORKDIR /app
COPY ./ProductionFiles /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the internal port (Must match the right side of -p in startup.sh)
EXPOSE 5000

# Start the application
CMD ["python3", "app.py"]