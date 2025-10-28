#!/bin/bash
# Script d'initialisation de Cassandra
# Crée le keyspace et les tables pour les données temps réel

echo "================================================"
echo "🔧 Initialisation de Cassandra"
echo "================================================"

# Attendre que Cassandra soit prêt
echo "⏳ Attente du démarrage de Cassandra..."
sleep 30

# Créer le keyspace et la table via cqlsh
echo "📊 Création du keyspace 'realtime'..."
cqlsh cassandra -e "
CREATE KEYSPACE IF NOT EXISTS realtime 
WITH REPLICATION = {
    'class' : 'SimpleStrategy', 
    'replication_factor' : 1
};
"

echo "📋 Création de la table 'recent_delays'..."
cqlsh cassandra -e "
USE realtime;

CREATE TABLE IF NOT EXISTS recent_delays (
    origin text PRIMARY KEY,
    recent_delay double,
    recent_dep_delay double
);
"

# Vérifier la création
echo "✓ Vérification des tables:"
cqlsh cassandra -e "
USE realtime;
DESCRIBE TABLES;
"

echo "📋 Schéma de la table 'recent_delays':"
cqlsh cassandra -e "
USE realtime;
DESCRIBE TABLE recent_delays;
"

echo "================================================"
echo "✅ Cassandra initialisé avec succès!"
echo "================================================"
