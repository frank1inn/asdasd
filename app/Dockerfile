FROM python:3.9-slim

WORKDIR /app

# Install curl for health checks and other dependencies
RUN apt-get update && \
    apt-get install -y curl build-essential wget && \
    rm -rf /var/lib/apt/lists/*

# Install TA-Lib library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements file and install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of your application code
COPY . .

# Add init_db.py
COPY init_db.py .

# Update CMD to run init_db first
CMD ["sh", "-c", "python init_db.py && python app.py"]
