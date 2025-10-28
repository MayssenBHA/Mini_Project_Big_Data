# Guide de Démarrage Rapide - Windows PowerShell

## 🚀 Démarrage en 5 Minutes

### Prérequis Vérification
```powershell
# Vérifier Docker
docker --version
docker compose version

# Vérifier les fichiers CSV
dir data\*.csv
```

---

## 📋 Commandes Essentielles (Copier-Coller)

### 1. Démarrer l'Infrastructure (2-5 min)
```powershell
# Dans le répertoire du projet
cd C:\Users\mayssen\bigdata-project

# Lancer tous les services
docker compose up -d

# Attendre que tout soit prêt (2-5 minutes)
Start-Sleep -Seconds 120

# Vérifier l'état
docker compose ps
```

### 2. Initialisation Complète (5-10 min)
```powershell
# Installer les dépendances Python
docker exec -it python-env python /scripts/install_dependencies.py

# Initialiser HDFS (charger les données)
docker exec -it hadoop-master bash -c "chmod +x /scripts/init_hdfs.sh && /scripts/init_hdfs.sh"

# Initialiser Kafka (créer le topic)
docker exec -it kafka bash -c "chmod +x /scripts/init_kafka.sh && /scripts/init_kafka.sh"

# Initialiser Cassandra (créer les tables)
docker exec -it cassandra bash -c "chmod +x /scripts/init_cassandra.sh && /scripts/init_cassandra.sh"

# Initialiser Hive (créer la base)
docker exec -it hive bash -c "chmod +x /scripts/init_hive.sh && /scripts/init_hive.sh"
```

### 3. Lancer le Batch Layer (Traitement Historique)
```powershell
# Soumettre le job Spark batch
docker exec -it spark-master spark-submit --master spark://spark-master:7077 --deploy-mode client /scripts/batch_job.py
```

### 4. Lancer le Speed Layer (Temps Réel)

**Terminal 1 - Spark Streaming:**
```powershell
# Mode console (pour voir les résultats)
docker exec -it spark-master spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,com.datastax.spark:spark-cassandra-connector_2.12:3.3.0 /scripts/streaming_job.py console

# OU Mode Cassandra (production)
docker exec -it spark-master spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,com.datastax.spark:spark-cassandra-connector_2.12:3.3.0 /scripts/streaming_job.py cassandra
```

**Terminal 2 - Producteur Kafka:**
```powershell
# Ouvrir un nouveau terminal PowerShell
cd C:\Users\mayssen\bigdata-project

# Lancer le producteur
docker exec -it python-env python /scripts/producer_flights.py
```

### 5. Vérifier les Résultats

**Hive (Batch):**
```powershell
# Se connecter à Hive
docker exec -it hive beeline -u jdbc:hive2://localhost:10000

# Dans Beeline, exécuter:
# USE batch_views;
# SELECT * FROM airport_delay_stats ORDER BY avg_delay DESC LIMIT 10;
# !quit
```

**Cassandra (Temps Réel):**
```powershell
# Se connecter à Cassandra
docker exec -it cassandra cqlsh

# Dans CQL, exécuter:
# USE realtime;
# SELECT * FROM recent_delays LIMIT 10;
# exit
```

**Kafka (Messages):**
```powershell
# Voir les messages Kafka
docker exec -it kafka kafka-console-consumer.sh --topic live-flights --from-beginning --bootstrap-server localhost:9092 --max-messages 5
```

---

## 🌐 Interfaces Web

```powershell
# Ouvrir les interfaces web
start http://localhost:9870  # HDFS
start http://localhost:8080  # Spark Master
```

---

## 🛑 Arrêter Proprement

```powershell
# Arrêter tous les services
docker compose down

# Arrêter et supprimer les volumes (ATTENTION: perte de données)
docker compose down -v
```

---

## 🔍 Monitoring en Temps Réel

```powershell
# Voir les logs en temps réel
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f spark-master

# Statistiques des conteneurs
docker stats
```

---

## ⚡ Commandes Rapides

```powershell
# Redémarrer un service
docker compose restart [service_name]

# Entrer dans un conteneur
docker exec -it [container_name] bash

# Voir l'utilisation des ressources
docker stats --no-stream

# Nettoyer Docker
docker system prune -a
```

---

## 🐛 Dépannage Express

**Problème: Conteneur ne démarre pas**
```powershell
docker compose logs [service_name]
docker compose restart [service_name]
```

**Problème: Port occupé**
```powershell
netstat -ano | findstr :[PORT]
# Arrêter le processus ou modifier docker-compose.yml
```

**Problème: Mémoire insuffisante**
```
Docker Desktop → Settings → Resources → Augmenter RAM à 8+ GB
```

**Redémarrage complet:**
```powershell
docker compose down
docker compose up -d
Start-Sleep -Seconds 120
docker compose ps
```

---

## 📊 Workflow Complet (Script Automatique)

Créez un fichier `run_full_pipeline.ps1`:

```powershell
# Script de lancement complet
Write-Host "🚀 Démarrage du pipeline Big Data..." -ForegroundColor Green

# 1. Démarrer les services
Write-Host "📦 Lancement des conteneurs..." -ForegroundColor Yellow
docker compose up -d
Start-Sleep -Seconds 120

# 2. Initialisation
Write-Host "⚙️ Initialisation..." -ForegroundColor Yellow
docker exec -it python-env python /scripts/install_dependencies.py
docker exec -it hadoop-master bash -c "/scripts/init_hdfs.sh"
docker exec -it kafka bash -c "/scripts/init_kafka.sh"
docker exec -it cassandra bash -c "/scripts/init_cassandra.sh"

# 3. Batch Layer
Write-Host "📊 Lancement du Batch Layer..." -ForegroundColor Yellow
docker exec -it spark-master spark-submit --master spark://spark-master:7077 /scripts/batch_job.py

Write-Host "✅ Pipeline prêt! Lancez manuellement le Speed Layer." -ForegroundColor Green
Write-Host "Terminal 1: docker exec -it spark-master spark-submit ... /scripts/streaming_job.py console" -ForegroundColor Cyan
Write-Host "Terminal 2: docker exec -it python-env python /scripts/producer_flights.py" -ForegroundColor Cyan
```

Exécuter:
```powershell
.\run_full_pipeline.ps1
```

---

**🎉 Vous êtes prêt! Happy Big Data Processing! 🚀**
