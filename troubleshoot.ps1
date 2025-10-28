# Script de diagnostic et dépannage
# Usage: .\troubleshoot.ps1

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   🔍 Diagnostic du Projet Big Data" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Fonction pour vérifier un service
function Test-Service {
    param($name, $container, $port, $url)
    
    Write-Host "🔍 Vérification de $name..." -ForegroundColor Cyan
    
    # Vérifier que le conteneur existe et tourne
    $status = docker inspect -f '{{.State.Running}}' $container 2>$null
    
    if ($status -eq "true") {
        Write-Host "  ✓ Conteneur $container est en cours d'exécution" -ForegroundColor Green
        
        # Vérifier le port si fourni
        if ($port) {
            $portCheck = netstat -an | Select-String ":$port.*LISTENING"
            if ($portCheck) {
                Write-Host "  ✓ Port $port est accessible" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Port $port n'est pas accessible" -ForegroundColor Yellow
            }
        }
        
        # Afficher l'URL si fournie
        if ($url) {
            Write-Host "  🌐 Interface: $url" -ForegroundColor Cyan
        }
    } elseif ($status -eq "false") {
        Write-Host "  ❌ Conteneur $container existe mais n'est pas démarré" -ForegroundColor Red
        Write-Host "     Redémarrez avec: docker compose restart $container" -ForegroundColor Yellow
    } else {
        Write-Host "  ❌ Conteneur $container n'existe pas" -ForegroundColor Red
        Write-Host "     Lancez avec: docker compose up -d" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Vérifier Docker
Write-Host "1️⃣  Vérification de Docker" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
try {
    $dockerVersion = docker --version
    Write-Host "  ✓ Docker: $dockerVersion" -ForegroundColor Green
    
    $composeVersion = docker compose version
    Write-Host "  ✓ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker n'est pas installé ou n'est pas accessible" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Vérifier les conteneurs
Write-Host "2️⃣  Vérification des Services" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray

Test-Service "Hadoop NameNode" "hadoop-master" 9870 "http://localhost:9870"
Test-Service "Hadoop DataNode" "hadoop-datanode" $null $null
Test-Service "Spark Master" "spark-master" 8080 "http://localhost:8080"
Test-Service "Spark Worker" "spark-worker" $null $null
Test-Service "Zookeeper" "zookeeper" 2181 $null
Test-Service "Kafka" "kafka" 9092 $null
Test-Service "Cassandra" "cassandra" 9042 $null
Test-Service "Hive" "hive" 10000 $null
Test-Service "Python Environment" "python-env" $null $null

# Vérifier les ressources
Write-Host "3️⃣  Utilisation des Ressources" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  Statistiques des conteneurs:" -ForegroundColor White
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null
Write-Host ""

# Vérifier les volumes
Write-Host "4️⃣  Volumes Docker" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
$volumes = docker volume ls --filter "name=bigdata-project" --format "{{.Name}}"
if ($volumes) {
    Write-Host "  Volumes créés:" -ForegroundColor White
    foreach ($vol in $volumes) {
        Write-Host "    • $vol" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠️  Aucun volume trouvé" -ForegroundColor Yellow
}
Write-Host ""

# Vérifier les données
Write-Host "5️⃣  Vérification des Données" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
if (Test-Path "data\*.csv") {
    $csvFiles = Get-ChildItem -Path "data" -Filter "*.csv"
    Write-Host "  ✓ Fichiers CSV trouvés: $($csvFiles.Count)" -ForegroundColor Green
    foreach ($file in $csvFiles | Select-Object -First 3) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-Host "    • $($file.Name) ($sizeMB MB)" -ForegroundColor Cyan
    }
    if ($csvFiles.Count -gt 3) {
        Write-Host "    • ... et $($csvFiles.Count - 3) autres fichiers" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠️  Aucun fichier CSV trouvé dans le dossier data/" -ForegroundColor Yellow
    Write-Host "     Téléchargez les données depuis Kaggle" -ForegroundColor Yellow
}
Write-Host ""

# Vérifier les logs pour erreurs
Write-Host "6️⃣  Recherche d'Erreurs dans les Logs" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
Write-Host "  Dernières erreurs par service:" -ForegroundColor White

$containers = @("hadoop-master", "spark-master", "kafka", "cassandra", "hive")
foreach ($container in $containers) {
    $errors = docker logs $container 2>&1 | Select-String -Pattern "ERROR|Exception|FATAL" | Select-Object -Last 1
    if ($errors) {
        Write-Host "    ⚠️  $container : $($errors.Line)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Recommandations
Write-Host "7️⃣  Recommandations" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Gray

$runningContainers = docker ps --format "{{.Names}}" | Measure-Object | Select-Object -ExpandProperty Count
$expectedContainers = 9

if ($runningContainers -lt $expectedContainers) {
    Write-Host "  ⚠️  Seulement $runningContainers/$expectedContainers conteneurs en cours d'exécution" -ForegroundColor Yellow
    Write-Host "     Action: docker compose up -d" -ForegroundColor Cyan
} else {
    Write-Host "  ✓ Tous les conteneurs sont en cours d'exécution" -ForegroundColor Green
}

# Vérifier la mémoire disponible
$memInfo = docker system df 2>$null
if ($memInfo) {
    Write-Host ""
    Write-Host "  💾 Espace Docker:" -ForegroundColor Cyan
    docker system df
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   🔧 Commandes de Dépannage Rapide" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Redémarrer tous les services:" -ForegroundColor White
Write-Host "    docker compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "  Voir les logs d'un service:" -ForegroundColor White
Write-Host "    docker compose logs -f [service_name]" -ForegroundColor Gray
Write-Host ""
Write-Host "  Redémarrage complet:" -ForegroundColor White
Write-Host "    docker compose down && docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "  Nettoyer et redémarrer (ATTENTION: perte de données):" -ForegroundColor White
Write-Host "    docker compose down -v && docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
