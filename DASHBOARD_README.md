# 📊 Dashboard Streamlit - Lambda Architecture

Dashboard interactif pour visualiser les données de l'architecture Lambda Big Data (Flight Delays Analysis).

## 🎯 Fonctionnalités

### 🗄️ **Batch Layer**
- **Vue historique complète** : 7,213,446 vols analysés (année 2018)
- **358 aéroports** avec statistiques détaillées
- **Top 20 aéroports** avec les retards les plus importants
- **Graphiques interactifs** : Retards moyens par aéroport

### ⚡ **Speed Layer**
- **Données temps réel** depuis Cassandra
- **Auto-refresh** : Mise à jour automatique toutes les 30 secondes
- **Retards actuels** par aéroport
- **Graphiques dynamiques** : Évolution en temps réel

### 🎯 **Serving Layer**
- **Comparaison Batch vs Speed** : Visualisation des différences
- **Recherche par aéroport** : Stats détaillées pour chaque aéroport
- **Analyse de corrélation** : Scatter plot historique vs temps réel
- **Top différences** : Retards augmentés ou diminués

## 🚀 Lancement Rapide

### Méthode 1: Script PowerShell (Recommandé)
```powershell
.\launch_dashboard.ps1
```

### Méthode 2: Manuelle
```powershell
# Démarrer les services Docker
docker compose up -d

# Lancer Streamlit
docker exec python-env streamlit run /scripts/dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true
```

### Méthode 3: En arrière-plan (PowerShell)
```powershell
Start-Job -ScriptBlock { 
    docker exec python-env streamlit run /scripts/dashboard.py `
        --server.port 8501 `
        --server.address 0.0.0.0 `
        --server.headless true 
} -Name "StreamlitDashboard"
```

## 🌐 Accès

Une fois lancé, le dashboard est accessible à :

**🔗 URL:** http://localhost:8501

Le dashboard s'ouvre automatiquement dans votre navigateur par défaut.

## 📋 Prérequis

### Services Docker requis
- ✅ **cassandra** : Base de données NoSQL (Speed Layer)
- ✅ **python-env** : Environnement Python avec Streamlit
- ✅ **kafka** : Streaming de données (optionnel pour la visualisation)

### Packages Python installés
```
streamlit==1.50.0
plotly==6.3.1
pandas==2.3.3
cassandra-driver==3.29.3
```

## 🎨 Interface

### Page d'accueil
- **Badges des 3 couches** : Batch, Speed, Serving
- **Métriques clés** : Nombre d'aéroports, vols analysés, retard moyen
- **Filtres sidebar** : Mode d'affichage, auto-refresh

### Vue d'ensemble
- **Top 20 Batch Layer** : Graphique en barres des retards historiques
- **Top 20 Speed Layer** : Graphique en barres des retards temps réel
- **Tableau détaillé** : Données complètes avec mise en forme

### Recherche par aéroport
- **Sélecteur d'aéroport** : Dropdown avec tous les aéroports
- **Comparaison visuelle** : Graphique côte à côte Batch vs Speed
- **Métriques détaillées** : Retard arrivée, retard départ

### Comparaison Batch vs Speed
- **Scatter plot** : Corrélation entre données historiques et temps réel
- **Top augmentés** : Aéroports avec retards augmentés
- **Top diminués** : Aéroports avec retards diminués
- **Ligne de référence** : Visualisation de l'écart

## 💡 Commandes Utiles

### Voir les logs du dashboard
```powershell
Receive-Job -Name "StreamlitDashboard" | Select-Object -Last 50
```

### Arrêter le dashboard
```powershell
Stop-Job -Name "StreamlitDashboard"
Remove-Job -Name "StreamlitDashboard"
```

### Relancer le dashboard
```powershell
.\launch_dashboard.ps1
```

### Vérifier le statut
```powershell
docker exec python-env ps aux | Select-String "streamlit"
```

## 🐛 Dépannage

### Le dashboard ne démarre pas
```powershell
# Vérifier les services Docker
docker compose ps

# Redémarrer python-env
docker compose restart python-env

# Vérifier les logs
docker logs python-env
```

### Erreur de connexion Cassandra
```powershell
# Vérifier que Cassandra tourne
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM realtime.recent_delays;"

# Redémarrer Cassandra si nécessaire
docker compose restart cassandra
```

### Port 8501 déjà utilisé
```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :8501

# Arrêter le processus (remplacer PID par le numéro trouvé)
taskkill /PID <PID> /F
```

### Données Speed Layer vides
```powershell
# Vérifier les données dans Cassandra
docker exec cassandra cqlsh -e "SELECT * FROM realtime.recent_delays LIMIT 10;"

# Si vide, relancer le consumer Kafka
docker exec python-env python /scripts/kafka_to_cassandra.py
```

## 📊 Captures d'écran

### Vue d'ensemble
- Top 20 aéroports avec graphiques interactifs
- Métriques globales en temps réel

### Recherche par aéroport
- Comparaison détaillée Batch vs Speed
- Graphiques côte à côte

### Analyse de corrélation
- Scatter plot avec ligne de référence
- Identification des outliers

## 🔧 Configuration

### Modifier le port
Dans `docker-compose.yml`:
```yaml
python-env:
  ports:
    - "8501:8501"  # Changer le premier port
```

### Personnaliser le cache
Dans `dashboard.py`:
```python
@st.cache_data(ttl=300)  # Cache 5 minutes
def load_batch_data():
    ...

@st.cache_data(ttl=30)  # Cache 30 secondes
def load_speed_data():
    ...
```

### Modifier l'auto-refresh
Dans le sidebar du dashboard:
- Cocher/décocher "🔄 Auto-refresh (30s)"
- L'intervalle est codé en dur dans le script

## 📈 Métriques Affichées

### Batch Layer
- **avg_delay** : Retard moyen à l'arrivée (minutes)
- **avg_dep_delay** : Retard moyen au départ (minutes)
- **total_flights** : Nombre total de vols
- **origin** : Code IATA de l'aéroport

### Speed Layer
- **recent_delay** : Retard récent à l'arrivée (minutes)
- **recent_dep_delay** : Retard récent au départ (minutes)
- **origin** : Code IATA de l'aéroport

### Calculs
- **Différence** : Speed - Batch
- **Corrélation** : Relation entre données historiques et temps réel

## 🎯 Cas d'Usage

### 1. Analyse historique
*"Quels sont les aéroports avec les retards les plus importants sur 2018?"*
→ Vue d'ensemble > Top 20 Batch Layer

### 2. Surveillance temps réel
*"Quels aéroports ont des retards actuellement?"*
→ Vue d'ensemble > Top 20 Speed Layer (avec auto-refresh)

### 3. Comparaison aéroport spécifique
*"Comment se comporte l'aéroport JFK historiquement vs maintenant?"*
→ Recherche par aéroport > Sélectionner JFK

### 4. Détection d'anomalies
*"Y a-t-il des aéroports avec des retards inhabituels par rapport à l'historique?"*
→ Comparaison Batch vs Speed > Scatter plot + Top différences

## 🚀 Améliorations Futures

- [ ] Export des données en CSV/Excel
- [ ] Notifications pour anomalies détectées
- [ ] Prévisions avec Machine Learning
- [ ] Filtres temporels avancés
- [ ] Carte interactive avec géolocalisation
- [ ] API REST pour interroger les données
- [ ] Authentification utilisateur

## 📝 Notes

- Le dashboard utilise des données **mockées** pour le Batch Layer (top 20 précalculés)
- Les données **Speed Layer** sont **réelles** depuis Cassandra
- Le cache est configuré pour optimiser les performances
- L'auto-refresh peut augmenter la charge sur Cassandra

## 📞 Support

En cas de problème:
1. Vérifier les logs: `Receive-Job -Name "StreamlitDashboard"`
2. Vérifier les services: `docker compose ps`
3. Consulter le README principal du projet
4. Consulter la documentation Streamlit: https://docs.streamlit.io

---

**Développé avec ❤️ pour le projet Lambda Architecture Big Data**
