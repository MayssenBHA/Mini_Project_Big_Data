#!/bin/bash
# Script d'initialisation de HDFS
# Crée les répertoires et charge les données CSV

echo "================================================"
echo "🔧 Initialisation de HDFS"
echo "================================================"

# Attendre que HDFS soit prêt
echo "⏳ Attente du démarrage de HDFS..."
sleep 15

# Créer les répertoires HDFS
echo "📁 Création des répertoires HDFS..."
hdfs dfs -mkdir -p /data/flights_raw
hdfs dfs -mkdir -p /user/hive/warehouse
hdfs dfs -mkdir -p /tmp

# Définir les permissions
echo "🔐 Configuration des permissions..."
hdfs dfs -chmod -R 777 /data
hdfs dfs -chmod -R 777 /user
hdfs dfs -chmod -R 777 /tmp

# Copier les fichiers CSV vers HDFS
echo "📤 Chargement des données CSV vers HDFS..."
if [ -f /data/2018.csv ]; then
    hdfs dfs -put -f /data/2018.csv /data/flights_raw/
    echo "✓ Fichier 2018.csv chargé"
else
    echo "⚠️  Fichier /data/2018.csv non trouvé"
fi

# Charger tous les fichiers CSV si présents
for file in /data/*.csv; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "2018.csv" ]; then
            echo "📤 Chargement de $filename..."
            hdfs dfs -put -f "$file" /data/flights_raw/
        fi
    fi
done

# Vérifier le contenu
echo "✓ Contenu de /data/flights_raw/:"
hdfs dfs -ls /data/flights_raw/

# Afficher l'espace utilisé
echo "💾 Espace utilisé dans HDFS:"
hdfs dfs -du -h /data/flights_raw/

echo "================================================"
echo "✅ HDFS initialisé avec succès!"
echo "================================================"
