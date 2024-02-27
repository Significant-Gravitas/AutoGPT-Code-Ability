#!/bin/zsh

docker compose down
docker compose up -d
poetry shell
rm -Rf migrations    
prisma migrate dev --name updates    
./run populate-db