#!/bin/bash

echo "Aguardando MongoDB inicializar..."
sleep 10

echo "Inicializando replica set..."
mongosh mongodb://mongo:27017 --eval "rs.initiate({ _id: 'rs0', members: [{ _id: 0, host: 'mongo:27017' }] })"

echo "Aguardando replica set se tornar PRIMARY..."
sleep 5

echo "Replica set configurado!"
