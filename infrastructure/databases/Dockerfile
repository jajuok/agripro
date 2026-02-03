# Dockerfile for Coolify deployment
# This file helps Coolify understand this is a valid application
FROM docker/compose:latest

WORKDIR /app

COPY docker-compose.yml .
COPY init-databases.sh .

# This is a meta-container - the actual deployment will use docker-compose
CMD ["version"]
