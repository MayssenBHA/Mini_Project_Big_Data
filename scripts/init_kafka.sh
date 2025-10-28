#!/bin/bash
# Script d'initialisation de Kafka
# Crée le topic pour les données de vols

echo "================================================"
echo "🔧 Initialisation de Kafka"
echo "================================================"

# Attendre que Kafka soit prêt
echo "⏳ Attente du démarrage de Kafka..."
sleep 10

# Créer le topic live-flights
echo "📡 Création du topic 'live-flights'..."
kafka-topics.sh --create \
    --topic live-flights \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

# Vérifier la création
echo "✓ Liste des topics:"
kafka-topics.sh --list --bootstrap-server localhost:9092

# Afficher les détails du topic
echo "📋 Détails du topic 'live-flights':"
kafka-topics.sh --describe \
    --topic live-flights \
    --bootstrap-server localhost:9092

echo "================================================"
echo "✅ Kafka initialisé avec succès!"
echo "================================================"
