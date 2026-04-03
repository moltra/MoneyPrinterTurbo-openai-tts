# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /MoneyPrinterTurbo-openai-tts

# 设置/MoneyPrinterTurbo-openai-tts目录权限为777
RUN mkdir -p /MoneyPrinterTurbo-openai-tts && chmod 777 /MoneyPrinterTurbo-openai-tts

ENV PYTHONPATH="/MoneyPrinterTurbo-openai-tts"

# Install system dependencies with domestic mirrors first for stability
RUN echo "deb http://mirrors.aliyun.com/debian bullseye main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bullseye-security main" >> /etc/apt/sources.list && \
    ( \
        for i in 1 2 3; do \
            echo "Attempt $i: Using Aliyun mirror"; \
            apt-get update && apt-get install -y --no-install-recommends \
                git \
                imagemagick \
                ffmpeg && break || \
            echo "Attempt $i failed, retrying..."; \
            if [ $i -eq 3 ]; then \
                echo "Aliyun mirror failed, switching to Tsinghua mirror"; \
                sed -i 's/mirrors.aliyun.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
                sed -i 's/mirrors.aliyun.com\/debian-security/mirrors.tuna.tsinghua.edu.cn\/debian-security/g' /etc/apt/sources.list && \
                ( \
                    apt-get update && apt-get install -y --no-install-recommends \
                        git \
                        imagemagick \
                        ffmpeg || \
                    ( \
                        echo "Tsinghua mirror failed, switching to default Debian mirror"; \
                        sed -i 's/mirrors.tuna.tsinghua.edu.cn/deb.debian.org/g' /etc/apt/sources.list && \
                        sed -i 's/mirrors.tuna.tsinghua.edu.cn\/debian-security/security.debian.org/g' /etc/apt/sources.list; \
                        apt-get update && apt-get install -y --no-install-recommends \
                            git \
                            imagemagick \
                            ffmpeg; \
                    ); \
                ); \
            fi; \
            sleep 5; \
        done \
    ) && rm -rf /var/lib/apt/lists/*

# Fix security policy for ImageMagick
RUN sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' /etc/ImageMagick-6/policy.xml

# Copy only the requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the codebase into the image
COPY . .

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "./webui/Main.py","--server.address=0.0.0.0","--server.enableCORS=True","--browser.gatherUsageStats=False"]

# 1. Build the Docker image using the following command
# docker build -t moneyprinterturbo-openai-tts .

# 2. Run the Docker container using the following command
## For Linux or MacOS:
# docker run -v $(pwd)/config.toml:/MoneyPrinterTurbo-openai-tts/config.toml -v $(pwd)/storage:/MoneyPrinterTurbo-openai-tts/storage -p 8501:8501 moneyprinterturbo-openai-tts
## For Windows:
# docker run -v ${PWD}/config.toml:/MoneyPrinterTurbo-openai-tts/config.toml -v ${PWD}/storage:/MoneyPrinterTurbo-openai-tts/storage -p 8501:8501 moneyprinterturbo-openai-tts