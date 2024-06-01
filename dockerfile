# Use an official Ubuntu image as the base
FROM ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the entire directory into the container
COPY . .

# Create a virtual environment
RUN python3 -m venv /venv

# Activate the virtual environment
ENV PATH="/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Streamlit runs on
EXPOSE 8501

# Define the command to run the Streamlit app
CMD ["streamlit", "run", "main.py"]
