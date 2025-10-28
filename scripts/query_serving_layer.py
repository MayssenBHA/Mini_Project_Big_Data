"""
Serving Layer - Requêtes combinées Batch + Speed
Combine les vues batch (Hive) et temps réel (Cassandra)
"""
import sys
from cassandra.cluster import Cluster
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_cassandra(host='cassandra', port=9042):
    """Se connecte à Cassandra"""
    try:
        cluster = Cluster([host], port=port)
        session = cluster.connect('realtime')
        logger.info("✓ Connecté à Cassandra")
        return cluster, session
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à Cassandra: {e}")
        return None, None

def query_realtime_delays(session, origin=None, limit=10):
    """
    Query les retards temps réel depuis Cassandra
    
    Args:
        session: Session Cassandra
        origin: Aéroport d'origine (optionnel)
        limit: Nombre de résultats
    """
    try:
        if origin:
            query = f"SELECT * FROM recent_delays WHERE origin = '{origin}'"
        else:
            query = f"SELECT * FROM recent_delays LIMIT {limit}"
        
        rows = session.execute(query)
        
        results = []
        for row in rows:
            results.append({
                'origin': row.origin,
                'recent_delay': row.recent_delay,
                'recent_dep_delay': row.recent_dep_delay
            })
        
        return results
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la requête: {e}")
        return []

def display_results(results, title="Résultats"):
    """Affiche les résultats de manière formatée"""
    logger.info(f"\n{'=' * 70}")
    logger.info(f"📊 {title}")
    logger.info('=' * 70)
    
    if not results:
        logger.info("Aucun résultat trouvé")
        return
    
    # Header
    logger.info(f"{'Aéroport':<15} {'Retard Récent (min)':<25} {'Retard Départ (min)':<25}")
    logger.info('-' * 70)
    
    # Rows
    for r in results:
        origin = r['origin'] or 'N/A'
        recent_delay = f"{r['recent_delay']:.2f}" if r['recent_delay'] is not None else 'N/A'
        recent_dep_delay = f"{r['recent_dep_delay']:.2f}" if r['recent_dep_delay'] is not None else 'N/A'
        logger.info(f"{origin:<15} {recent_delay:<25} {recent_dep_delay:<25}")
    
    logger.info('=' * 70)

def main():
    """Fonction principale"""
    logger.info("=" * 70)
    logger.info("🔍 Serving Layer - Requêtes Temps Réel")
    logger.info("=" * 70)
    
    # Connexion à Cassandra
    cluster, session = connect_cassandra()
    
    if session is None:
        logger.error("Impossible de se connecter à Cassandra")
        sys.exit(1)
    
    # Exemple de requêtes
    try:
        # 1. Top 10 aéroports avec retards récents
        logger.info("\n📌 Top 10 aéroports avec retards récents:")
        results = query_realtime_delays(session, limit=10)
        display_results(results, "Top 10 Aéroports - Retards Temps Réel")
        
        # 2. Requête spécifique (exemple: JFK)
        logger.info("\n📌 Requête pour un aéroport spécifique (JFK):")
        results = query_realtime_delays(session, origin='JFK')
        display_results(results, "Aéroport JFK - Retards Temps Réel")
        
        # Instructions pour combiner avec Hive
        logger.info("\n" + "=" * 70)
        logger.info("📚 Pour combiner avec les données batch (Hive):")
        logger.info("=" * 70)
        logger.info("1. Connectez-vous à Hive:")
        logger.info("   docker exec -it hive beeline -u jdbc:hive2://localhost:10000")
        logger.info("\n2. Exécutez la requête:")
        logger.info("   USE batch_views;")
        logger.info("   SELECT * FROM airport_delay_stats WHERE origin = 'JFK';")
        logger.info("\n3. Comparez les résultats batch (historique) vs temps réel!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
    finally:
        cluster.shutdown()
        logger.info("\n✓ Connexion fermée")

if __name__ == "__main__":
    main()
