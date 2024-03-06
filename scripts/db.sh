#!/bin/zsh

docker compose down
docker compose up -d
rm -Rf migrations    
poetry run prisma migrate dev --name updates    
./run populate-db