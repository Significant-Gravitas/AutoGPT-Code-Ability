#!/bin/zsh

docker compose down
docker compose up -d postgres
rm -Rf migrations    
poetry run prisma migrate dev --name updates    
./run populate-db