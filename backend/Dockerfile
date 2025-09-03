FROM python:3.12-slim

# Set environment variables to optimize Python performance and Docker build
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . /app/

# Expose the port your Django application will run on (e.g., 8000 for development server)
EXPOSE 8000

# Используем entrypoint.sh для миграций и запуска
ENTRYPOINT ["./entrypoint.sh"]
