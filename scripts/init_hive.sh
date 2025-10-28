#!/bin/bash
# Script d'initialisation de Hive
# Crée la base de données pour les vues batch

echo "================================================"
echo "🔧 Initialisation de Hive"
echo "================================================"

# Attendre que Hive soit prêt
echo "⏳ Attente du démarrage de Hive..."
sleep 20

# Créer la base de données
echo "📊 Création de la base de données 'batch_views'..."
beeline -u jdbc:hive2://localhost:10000 -e "
CREATE DATABASE IF NOT EXISTS batch_views
COMMENT 'Base de données pour les vues batch de l architecture Lambda'
LOCATION '/user/hive/warehouse/batch_views.db';
"

# Vérifier la création
echo "✓ Liste des bases de données:"
beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"

echo "================================================"
echo "✅ Hive initialisé avec succès!"
echo "================================================"
