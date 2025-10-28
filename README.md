# 🚀 Projet Big Data - Prédiction des Retards de Vols
## Architecture Lambda avec Docker

Ce projet implémente une **Architecture Lambda** complète pour l'analyse et la prédiction des retards de vols en utilisant les technologies Big Data modernes, le tout orchestré avec Docker.

---

## 📋 Table des Matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Architecture](#-architecture)
3. [Technologies](#-technologies)
4. [Prérequis](#-prérequis)
5. [Installation](#-installation)
6. [Configuration](#-configuration)
7. [Utilisation](#-utilisation)
8. [Structure du Projet](#-structure-du-projet)
9. [Commandes Utiles](#-commandes-utiles)
10. [Dépannage](#-dépannage)

---

## 🎯 Vue d'ensemble

Ce projet analyse les données de vols des compagnies aériennes américaines pour prédire les retards. Il utilise l'architecture Lambda qui combine:
- **Batch Layer**: Traitement historique massif avec Spark et stockage dans Hive
- **Speed Layer**: Traitement temps réel avec Kafka et Spark Streaming vers Cassandra
- **Serving Layer**: Combinaison des vues batch et temps réel pour requêtes optimales

### Dataset
- **Source**: [Kaggle - Airline Delay and Cancellation Data (2009-2018)](https://www.kaggle.com/datasets/yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018)
- **Taille**: ~5-10 GB (tous les fichiers CSV)
- **Lignes**: ~7 millions par année
- **Colonnes**: 28 attributs (retards, aéroports, distances, etc.)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Architecture Lambda                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Dataset    │ (CSV Files)
│  Flights     │
└──────┬───────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│   BATCH LAYER    │              │   SPEED LAYER    │
│                  │              │                  │
│  HDFS Storage    │              │  Kafka Ingestion │
│       ↓          │              │       ↓          │
│  Spark Batch     │              │ Spark Streaming  │
│       ↓          │              │       ↓          │
│  Hive Tables     │              │    Cassandra     │
└────────┬─────────┘              └────────┬─────────┘
         │                                 │
         └────────────┬────────────────────┘
                      ▼
              ┌──────────────────┐
              │  SERVING LAYER   │
              │                  │
              │  Query Engine    │
              │  (Hive + CQL)    │
              └──────────────────┘
```

---

## 🛠️ Technologies

| Composant | Technologie | Version | Port |
|-----------|-------------|---------|------|
| **Stockage Distribué** | Apache Hadoop (HDFS) | 3.1.1 | 9870, 9000 |
| **Traitement Batch** | Apache Spark | 3.3.0 | 8080, 7077 |
| **Message Broker** | Apache Kafka | 7.0.1 | 9092, 29092 |
| **Coordination** | Apache Zookeeper | 7.0.1 | 2181 |
| **NoSQL Temps Réel** | Apache Cassandra | 4.0 | 9042 |
| **Data Warehouse** | Apache Hive | 2.3.2 | 10000 |
| **Scripting** | Python | 3.9 | - |
| **Orchestration** | Docker Compose | 3 | - |

---

## 💻 Prérequis

### Système Hôte
- **OS**: Windows 10/11, macOS, ou Linux (Ubuntu 20.04+)
- **RAM**: **Minimum 16 GB** (recommandé 32 GB)
- **Disque**: **Minimum 50 GB** d'espace libre
- **CPU**: 4 cœurs minimum (recommandé 8 cœurs)

### Logiciels
- **Docker Desktop** (dernière version)
  - Windows/Mac: [Télécharger ici](https://www.docker.com/products/docker-desktop)
  - Linux: Docker Engine + Docker Compose
- **Git** (pour cloner le projet)

### Vérification
```powershell
# Vérifier Docker
docker --version
docker compose version

# Vérifier les ressources Docker Desktop
# Ouvrir Docker Desktop → Settings → Resources
# Allouer au moins 8 GB RAM et 4 CPU cores
```

---

## 📥 Installation

### Étape 1: Cloner ou Créer le Projet
```powershell
# Si le projet existe déjà
cd C:\Users\mayssen\bigdata-project

# Sinon, créer la structure
mkdir bigdata-project
cd bigdata-project
mkdir data, scripts, configs, configs\hive
```

### Étape 2: Télécharger le Dataset
1. Allez sur [Kaggle](https://www.kaggle.com/datasets/yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018)
2. Téléchargez le ZIP (~5 GB)
3. Extrayez les fichiers CSV dans `data/`
4. Pour tests, utilisez `2018.csv` (~7M lignes)

```powershell
# Vérifier que les données sont présentes
dir data\*.csv
```

### Étape 3: Lancer l'Infrastructure
```powershell
# Lancer tous les conteneurs
docker compose up -d

# Vérifier que tous les services sont démarrés (peut prendre 2-5 minutes)
docker compose ps

# Vous devriez voir 8 conteneurs: hadoop-master, hadoop-datanode, 
# spark-master, spark-worker, kafka, zookeeper, cassandra, hive, python-env
```

### Étape 4: Attendre l'Initialisation
```powershell
# Attendre que tous les services soient prêts (2-5 minutes)
# Vérifier les logs
docker compose logs -f
# Appuyer sur Ctrl+C pour sortir

# Vérifier les interfaces web
# HDFS: http://localhost:9870
# Spark: http://localhost:8080
```

---

## ⚙️ Configuration

### 1. Initialiser HDFS
```powershell
# Charger les données dans HDFS
docker exec -it hadoop-master bash
/scripts/init_hdfs.sh
exit
```

### 2. Initialiser Kafka
```powershell
# Créer le topic Kafka
docker exec -it kafka bash
/scripts/init_kafka.sh
exit
```

### 3. Initialiser Cassandra
```powershell
# Créer le keyspace et la table
docker exec -it cassandra bash
/scripts/init_cassandra.sh
exit
```

### 4. Initialiser Hive
```powershell
# Créer la base de données
docker exec -it hive bash
/scripts/init_hive.sh
exit
```

### 5. Installer les Dépendances Python
```powershell
# Installer kafka-python, pandas, etc.
docker exec -it python-env python /scripts/install_dependencies.py
```

---

## 🎮 Utilisation

### Flux Complet End-to-End

#### 1️⃣ Batch Layer (Traitement Historique)
```powershell
# Soumettre le job batch Spark
docker exec -it spark-master spark-submit `
  --master spark://spark-master:7077 `
  --deploy-mode client `
  /scripts/batch_job.py

# Vérifier les résultats dans Hive
docker exec -it hive beeline -u jdbc:hive2://localhost:10000
# Dans Beeline:
> SHOW DATABASES;
> USE batch_views;
> SHOW TABLES;
> SELECT * FROM airport_delay_stats ORDER BY avg_delay DESC LIMIT 10;
> !quit
```

#### 2️⃣ Speed Layer (Streaming Temps Réel)

**Terminal 1: Lancer le Streaming Job**
```powershell
# Lancer Spark Streaming (console mode pour debug)
docker exec -it spark-master spark-submit `
  --master spark://spark-master:7077 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,com.datastax.spark:spark-cassandra-connector_2.12:3.3.0 `
  /scripts/streaming_job.py console

# OU vers Cassandra (production)
docker exec -it spark-master spark-submit `
  --master spark://spark-master:7077 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,com.datastax.spark:spark-cassandra-connector_2.12:3.3.0 `
  /scripts/streaming_job.py cassandra
```

**Terminal 2: Lancer le Producteur Kafka**
```powershell
# Ingérer les données vers Kafka
docker exec -it python-env python /scripts/producer_flights.py

# Avec un fichier spécifique
docker exec -it python-env python /scripts/producer_flights.py /data/2018.csv live-flights
```

**Vérifier Kafka**
```powershell
# Consommer les messages (autre terminal)
docker exec -it kafka kafka-console-consumer.sh `
  --topic live-flights `
  --from-beginning `
  --bootstrap-server localhost:9092 `
  --max-messages 10
```

#### 3️⃣ Serving Layer (Requêtes Combinées)

**Query Cassandra (Temps Réel)**
```powershell
docker exec -it cassandra cqlsh
# Dans CQL:
> USE realtime;
> SELECT * FROM recent_delays WHERE origin = 'JFK';
> SELECT * FROM recent_delays ORDER BY recent_delay DESC LIMIT 10;
> exit
```

**Query Hive (Batch)**
```powershell
docker exec -it hive beeline -u jdbc:hive2://localhost:10000
# Dans Beeline:
> USE batch_views;
> SELECT origin, avg_delay, total_flights, delay_rate 
  FROM airport_delay_stats 
  WHERE origin = 'JFK';
> !quit
```

---

## 📁 Structure du Projet

```
bigdata-project/
├── docker-compose.yml          # Orchestration des services
├── data/                       # Données CSV (à télécharger)
│   ├── 2018.csv               # Données de vols 2018
│   └── ...                    # Autres années si besoin
├── scripts/                   # Scripts Python et Bash
│   ├── producer_flights.py    # Producteur Kafka
│   ├── batch_job.py          # Job Spark batch
│   ├── streaming_job.py      # Job Spark streaming
│   ├── init_kafka.sh         # Init Kafka
│   ├── init_cassandra.sh     # Init Cassandra
│   ├── init_hdfs.sh          # Init HDFS
│   ├── init_hive.sh          # Init Hive
│   └── install_dependencies.py # Install Python packages
├── configs/                   # Configurations
│   └── hive/                 # Configs Hive (si besoin)
└── README.md                 # Ce fichier
```

---

## 🔧 Commandes Utiles

### Docker Compose
```powershell
# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Voir les logs
docker compose logs -f [service_name]

# Redémarrer un service
docker compose restart [service_name]

# Voir l'état des conteneurs
docker compose ps
```

### Accès aux Conteneurs
```powershell
# Hadoop
docker exec -it hadoop-master bash

# Spark
docker exec -it spark-master bash

# Kafka
docker exec -it kafka bash

# Cassandra
docker exec -it cassandra cqlsh

# Hive
docker exec -it hive beeline -u jdbc:hive2://localhost:10000

# Python
docker exec -it python-env bash
```

### Monitoring
```powershell
# HDFS Web UI
start http://localhost:9870

# Spark Master UI
start http://localhost:8080

# Statistiques Docker
docker stats
```

### HDFS
```powershell
# Lister les fichiers
docker exec -it hadoop-master hdfs dfs -ls /data/flights_raw

# Voir le contenu d'un fichier
docker exec -it hadoop-master hdfs dfs -cat /data/flights_raw/2018.csv | head

# Espace utilisé
docker exec -it hadoop-master hdfs dfs -du -h /data
```

### Kafka
```powershell
# Lister les topics
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Détails d'un topic
docker exec -it kafka kafka-topics.sh --describe --topic live-flights --bootstrap-server localhost:9092

# Consommer des messages
docker exec -it kafka kafka-console-consumer.sh --topic live-flights --from-beginning --bootstrap-server localhost:9092 --max-messages 5
```

### Cassandra
```powershell
# Se connecter
docker exec -it cassandra cqlsh

# Commandes CQL
DESCRIBE KEYSPACES;
USE realtime;
DESCRIBE TABLES;
SELECT COUNT(*) FROM recent_delays;
```

---

## 🐛 Dépannage

### Problème: Les conteneurs ne démarrent pas
```powershell
# Vérifier les logs
docker compose logs

# Redémarrer proprement
docker compose down
docker compose up -d
```

### Problème: Mémoire insuffisante
```powershell
# Ouvrir Docker Desktop → Settings → Resources
# Augmenter la RAM à 8-12 GB minimum
# Redémarrer Docker Desktop
```

### Problème: Port déjà utilisé
```powershell
# Vérifier les ports
netstat -ano | findstr :9870
netstat -ano | findstr :8080

# Arrêter le processus qui utilise le port
# Ou modifier les ports dans docker-compose.yml
```

### Problème: HDFS n'est pas accessible
```powershell
# Vérifier que Hadoop est démarré
docker compose ps hadoop-master

# Redémarrer HDFS
docker compose restart hadoop-master hadoop-datanode

# Attendre 30 secondes et vérifier
start http://localhost:9870
```

### Problème: Spark ne peut pas se connecter à HDFS
```powershell
# Vérifier la configuration réseau
docker network ls
docker network inspect bigdata-project_bigdata

# Redémarrer Spark
docker compose restart spark-master spark-worker
```

### Problème: Kafka timeout
```powershell
# Vérifier que Zookeeper est démarré
docker compose ps zookeeper

# Redémarrer Kafka
docker compose restart zookeeper kafka

# Attendre 15 secondes
```

### Problème: Cassandra ne répond pas
```powershell
# Cassandra peut prendre 1-2 minutes au démarrage
docker compose logs cassandra

# Attendre le message "Starting listening for CQL clients"
# Puis tester:
docker exec -it cassandra cqlsh
```

### Nettoyage Complet
```powershell
# Arrêter et supprimer tous les conteneurs et volumes
docker compose down -v

# Supprimer les images (optionnel)
docker system prune -a

# Redémarrer from scratch
docker compose up -d
```

---

## 📊 Résultats Attendus

### Batch Layer
- Table Hive `batch_views.airport_delay_stats` avec statistiques par aéroport
- Colonnes: Origin, avg_delay, avg_dep_delay, total_flights, delayed_flights, delay_rate
- ~300+ aéroports analysés

### Speed Layer
- Table Cassandra `realtime.recent_delays` mise à jour en temps réel
- Colonnes: origin (PK), recent_delay, recent_dep_delay
- Latence < 5 secondes

### Serving Layer
- Requêtes combinées pour avoir vue complète (historique + temps réel)
- API ou dashboard (à implémenter) pour visualisation

---

## 📝 Prochaines Étapes

1. **Machine Learning**: Ajouter un modèle de prédiction (Random Forest, Gradient Boosting)
2. **Visualisation**: Dashboard avec Grafana ou Superset
3. **API REST**: Exposer les données via FastAPI ou Flask
4. **Automatisation**: Orchestration avec Airflow
5. **Monitoring**: Prometheus + Grafana pour métriques système

---

## 🤝 Contribution

Pour toute question ou amélioration, créez une issue ou un pull request.

---

## 📄 Licence

Ce projet est à des fins éducatives.

---

**Bon apprentissage! 🚀**
