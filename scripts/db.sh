#!/bin/zsh

docker compose down
docker compose up -d postgres
poetry run prisma migrate deploy
./run populate-db