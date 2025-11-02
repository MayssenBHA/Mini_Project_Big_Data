# Script de lancement du Dashboard Streamlit
# Lambda Architecture - Big Data Flight Delays

Write-Host "`n" -NoNewline
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  ✈️  LAMBDA ARCHITECTURE DASHBOARD - Big Data Flight Delays  ✈️" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Vérifier si les conteneurs sont démarrés
Write-Host "🔍 Vérification de l'infrastructure..." -ForegroundColor Yellow
$containers = docker compose ps --format json | ConvertFrom-Json

$required = @("cassandra", "python-env", "kafka")
$allRunning = $true

foreach ($service in $required) {
    $container = $containers | Where-Object { $_.Service -eq $service }
    if ($container -and $container.State -eq "running") {
        Write-Host "  ✅ $service : Running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $service : Not running" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host "`n⚠️  Certains services ne sont pas démarrés." -ForegroundColor Yellow
    Write-Host "Voulez-vous les démarrer maintenant? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        Write-Host "`n🚀 Démarrage des services..." -ForegroundColor Cyan
        docker compose up -d
        Write-Host "⏳ Attente du démarrage complet (30s)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    } else {
        Write-Host "`n❌ Lancement annulé." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 Lancement du Dashboard Streamlit..." -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Arrêter l'ancien job si il existe
Stop-Job -Name "StreamlitDashboard" -ErrorAction SilentlyContinue | Out-Null
Remove-Job -Name "StreamlitDashboard" -ErrorAction SilentlyContinue | Out-Null

# Démarrer Streamlit en arrière-plan
Start-Job -ScriptBlock { 
    docker exec python-env streamlit run /scripts/dashboard.py `
        --server.port 8501 `
        --server.address 0.0.0.0 `
        --server.headless true `
        --browser.gatherUsageStats false
} -Name "StreamlitDashboard" | Out-Null

Write-Host "⏳ Initialisation du dashboard (15s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Vérifier que Streamlit tourne
$process = docker exec python-env ps aux | Select-String "streamlit"
if ($process) {
    Write-Host "`n✅ Dashboard démarré avec succès!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Erreur lors du démarrage du dashboard" -ForegroundColor Red
    Write-Host "Logs:" -ForegroundColor Yellow
    Receive-Job -Name "StreamlitDashboard"
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "  🌐  DASHBOARD ACCESSIBLE" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "  📍 URL Locale : " -NoNewline -ForegroundColor Cyan
Write-Host "http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 FONCTIONNALITÉS DU DASHBOARD:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  🗄️  BATCH LAYER:" -ForegroundColor Blue
Write-Host "     • Top 20 aéroports avec plus de retards (historique 2018)"
Write-Host "     • 7.2M vols analysés sur 358 aéroports"
Write-Host "     • Statistiques détaillées par aéroport"
Write-Host ""
Write-Host "  ⚡ SPEED LAYER:" -ForegroundColor Red
Write-Host "     • Données temps réel depuis Cassandra"
Write-Host "     • Mise à jour automatique (30s)"
Write-Host "     • Retards actuels par aéroport"
Write-Host ""
Write-Host "  🎯 SERVING LAYER:" -ForegroundColor Magenta
Write-Host "     • Comparaison Batch vs Speed"
Write-Host "     • Recherche par aéroport"
Write-Host "     • Analyse des différences historique vs temps réel"
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 COMMANDES UTILES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  • Voir les logs     : " -NoNewline
Write-Host "Receive-Job -Name 'StreamlitDashboard' | Select-Object -Last 20" -ForegroundColor White
Write-Host ""
Write-Host "  • Arrêter dashboard : " -NoNewline
Write-Host "Stop-Job -Name 'StreamlitDashboard'" -ForegroundColor White
Write-Host ""
Write-Host "  • Relancer          : " -NoNewline
Write-Host ".\launch_dashboard.ps1" -ForegroundColor White
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Ouvrir automatiquement le navigateur
Write-Host "🌐 Ouverture du dashboard dans le navigateur..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "✅ Dashboard lancé! Appuyez sur une touche pour quitter..." -ForegroundColor Green
Write-Host "   (Le dashboard continuera de tourner en arrière-plan)" -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
