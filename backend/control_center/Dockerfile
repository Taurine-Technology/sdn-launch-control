FROM python:3.10

# Ensure that output is sent straight to terminal (without buffering)
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/app/

# Install system dependencies
RUN apt-get update  \
    && apt-get install -y ansible  \
    && apt-get install -y openssh-server  \
    && apt-get install -y ssh  \
    && apt-get install -y sshpass  \
    && apt-get install -y python3-dev  \
    && apt-get install -y gcc  \
    && apt-get install -y build-essential  \
    && apt-get install -y libpq-dev  \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
COPY requirements.yml ./
RUN ansible-galaxy collection install -r requirements.yml
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .