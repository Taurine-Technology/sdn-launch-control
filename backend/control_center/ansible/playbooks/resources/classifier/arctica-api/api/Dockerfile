# Use the Tensorflow 2.11 Python runtime as a parent image
FROM tensorflow/tensorflow:2.11.0-gpu

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . ./

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run the command to start gunicorn server
CMD ["gunicorn", "--reload", "-b", "0.0.0.0:5000", "app:app"]

