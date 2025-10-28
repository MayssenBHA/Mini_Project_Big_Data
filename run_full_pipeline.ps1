# Script PowerShell pour lancer automatiquement le pipeline Big Data
# Usage: .\run_full_pipeline.ps1

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   🚀 Pipeline Big Data - Architecture Lambda" -ForegroundColor Green
Write-Host "   📊 Prédiction des Retards de Vols" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que nous sommes dans le bon répertoire
if (-Not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Erreur: docker-compose.yml non trouvé!" -ForegroundColor Red
    Write-Host "   Assurez-vous d'être dans le répertoire du projet" -ForegroundColor Yellow
    exit 1
}

# Vérifier que Docker est installé
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker n'est pas installé ou n'est pas accessible" -ForegroundColor Red
    exit 1
}

# Fonction pour afficher une étape
function Show-Step {
    param($number, $title)
    Write-Host ""
    Write-Host "[$number/6] $title" -ForegroundColor Yellow
    Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
}

# Fonction pour attendre avec barre de progression
function Wait-WithProgress {
    param($seconds, $message)
    Write-Host "$message (${seconds}s)..." -ForegroundColor Cyan
    for ($i = 0; $i -lt $seconds; $i++) {
        Write-Progress -Activity $message -Status "Temps restant: $($seconds - $i) secondes" -PercentComplete (($i / $seconds) * 100)
        Start-Sleep -Seconds 1
    }
    Write-Progress -Activity $message -Completed
}

# Étape 1: Démarrer les conteneurs
Show-Step 1 "📦 Démarrage des conteneurs Docker"
Write-Host "   Lancement de tous les services (Hadoop, Spark, Kafka, Cassandra, Hive)..." -ForegroundColor White
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du démarrage des conteneurs" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Conteneurs démarrés" -ForegroundColor Green

# Attendre que les services soient prêts
Wait-WithProgress 120 "⏳ Attente de l'initialisation des services"

# Vérifier l'état des conteneurs
Write-Host "`n📋 État des conteneurs:" -ForegroundColor Cyan
docker compose ps

# Étape 2: Installer les dépendances Python
Show-Step 2 "📦 Installation des dépendances Python"
Write-Host "   Installation de kafka-python, pandas, cassandra-driver..." -ForegroundColor White
docker exec python-env python /scripts/install_dependencies.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Avertissement: Erreur lors de l'installation des dépendances" -ForegroundColor Yellow
}
Write-Host "✓ Dépendances installées" -ForegroundColor Green

# Étape 3: Initialiser HDFS
Show-Step 3 "🗄️  Initialisation de HDFS"
Write-Host "   Création des répertoires et chargement des données CSV..." -ForegroundColor White
docker exec hadoop-master bash /scripts/init_hdfs.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Avertissement: Erreur lors de l'initialisation de HDFS" -ForegroundColor Yellow
}
Write-Host "✓ HDFS initialisé" -ForegroundColor Green

# Étape 4: Initialiser Kafka
Show-Step 4 "📡 Initialisation de Kafka"
Write-Host "   Création du topic 'live-flights'..." -ForegroundColor White
docker exec kafka bash /scripts/init_kafka.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Avertissement: Erreur lors de l'initialisation de Kafka" -ForegroundColor Yellow
}
Write-Host "✓ Kafka initialisé" -ForegroundColor Green

# Étape 5: Initialiser Cassandra
Show-Step 5 "💾 Initialisation de Cassandra"
Write-Host "   Création du keyspace 'realtime' et de la table 'recent_delays'..." -ForegroundColor White
Start-Sleep -Seconds 30  # Cassandra prend plus de temps à démarrer
docker exec cassandra bash /scripts/init_cassandra.sh
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Avertissement: Erreur lors de l'initialisation de Cassandra" -ForegroundColor Yellow
}
Write-Host "✓ Cassandra initialisé" -ForegroundColor Green

# Étape 6: Lancer le Batch Layer
Show-Step 6 "📊 Lancement du Batch Layer (Spark)"
Write-Host "   Traitement des données historiques et création des vues batch..." -ForegroundColor White
Write-Host "   Cela peut prendre plusieurs minutes selon la taille du dataset..." -ForegroundColor Cyan
docker exec spark-master spark-submit --master spark://spark-master:7077 --deploy-mode client /scripts/batch_job.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Avertissement: Erreur lors de l'exécution du batch job" -ForegroundColor Yellow
} else {
    Write-Host "✓ Batch Layer terminé avec succès" -ForegroundColor Green
}

# Résumé
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   ✅ INITIALISATION TERMINÉE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Prochaines étapes:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1️⃣  Lancer le Speed Layer (Streaming):" -ForegroundColor White
Write-Host "       Terminal 1 - Spark Streaming (console mode):" -ForegroundColor Cyan
Write-Host '       docker exec -it spark-master spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,com.datastax.spark:spark-cassandra-connector_2.12:3.3.0 /scripts/streaming_job.py console' -ForegroundColor Gray
Write-Host ""
Write-Host "       Terminal 2 - Producteur Kafka:" -ForegroundColor Cyan
Write-Host '       docker exec -it python-env python /scripts/producer_flights.py' -ForegroundColor Gray
Write-Host ""
Write-Host "   2️⃣  Vérifier les résultats:" -ForegroundColor White
Write-Host "       • HDFS UI:     http://localhost:9870" -ForegroundColor Cyan
Write-Host "       • Spark UI:    http://localhost:8080" -ForegroundColor Cyan
Write-Host "       • Hive Query:  docker exec -it hive beeline -u jdbc:hive2://localhost:10000" -ForegroundColor Gray
Write-Host "       • Cassandra:   docker exec -it cassandra cqlsh" -ForegroundColor Gray
Write-Host ""
Write-Host "   3️⃣  Arrêter le pipeline:" -ForegroundColor White
Write-Host "       docker compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   📚 Consultez README.md pour plus de détails" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
