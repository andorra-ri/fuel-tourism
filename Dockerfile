# Image to run the calculation as a Cloud Run Job (see docs/cloud.md)
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The settings and the stage are given as arguments of the job, ex:  --settings settings_2026 --stage all
# The logs go to the standard output.
ENTRYPOINT ["python", "main.py"]
