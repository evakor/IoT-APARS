FROM python:3.10

# Update the package list and install essential tools
RUN apt-get update && \
    apt-get install -y \
    vim \
    telnet \
    inetutils-ping

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pip==24.0

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose port for communication (e.g., MQTT or webhooks)
EXPOSE 9002

# Command to run the main script
CMD ["python3", "main.py"]
