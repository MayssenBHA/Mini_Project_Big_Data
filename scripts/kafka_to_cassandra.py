"""
Consumer Kafka qui écrit directement dans Cassandra
Alternative au Spark Streaming pour persister les données temps réel
"""
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
import json
import logging
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_cassandra_session():
    """Crée une session Cassandra"""
    cluster = Cluster(['cassandra'])
    session = cluster.connect('realtime')
    logger.info("✓ Connexion Cassandra établie")
    return cluster, session

def aggregate_delays(messages):
    """
    Agrège les retards par aéroport d'origine
    
    Args:
        messages: Liste de messages de vols
    Returns:
        Dict avec origin comme clé et stats comme valeur
    """
    airport_delays = defaultdict(lambda: {'arr_delays': [], 'dep_delays': []})
    
    for msg in messages:
        try:
            flight = json.loads(msg.value.decode('utf-8'))
            origin = flight.get('ORIGIN')
            arr_delay = flight.get('ARR_DELAY')
            dep_delay = flight.get('DEP_DELAY')
            cancelled = flight.get('CANCELLED', 0)
            
            # Filtrer les vols annulés
            if cancelled == 0 and origin and arr_delay is not None and dep_delay is not None:
                airport_delays[origin]['arr_delays'].append(arr_delay)
                airport_delays[origin]['dep_delays'].append(dep_delay)
        except Exception as e:
            logger.error(f"Erreur parsing message: {e}")
            continue
    
    # Calculer les moyennes
    aggregated = {}
    for origin, delays in airport_delays.items():
        if delays['arr_delays']:
            aggregated[origin] = {
                'recent_delay': sum(delays['arr_delays']) / len(delays['arr_delays']),
                'recent_dep_delay': sum(delays['dep_delays']) / len(delays['dep_delays'])
            }
    
    return aggregated

def write_to_cassandra(session, aggregated_data):
    """Écrit les données agrégées dans Cassandra"""
    insert_query = """
        INSERT INTO recent_delays (origin, recent_delay, recent_dep_delay)
        VALUES (?, ?, ?)
    """
    prepared = session.prepare(insert_query)
    prepared.consistency_level = ConsistencyLevel.ONE
    
    count = 0
    for origin, stats in aggregated_data.items():
        try:
            session.execute(prepared, (
                origin,
                float(stats['recent_delay']),
                float(stats['recent_dep_delay'])
            ))
            count += 1
        except Exception as e:
            logger.error(f"Erreur écriture Cassandra pour {origin}: {e}")
    
    return count

def run_consumer(kafka_servers='kafka:9092', topic='live-flights', batch_size=100):
    """
    Consomme depuis Kafka et écrit dans Cassandra par batch
    
    Args:
        kafka_servers: Adresse Kafka
        topic: Topic Kafka
        batch_size: Nombre de messages à agréger avant écriture
    """
    logger.info("=" * 60)
    logger.info("🚀 Démarrage Consumer Kafka → Cassandra")
    logger.info("=" * 60)
    
    # Connexion Cassandra
    cluster, session = create_cassandra_session()
    
    # Connexion Kafka
    logger.info(f"📡 Connexion à Kafka: {kafka_servers}, topic: {topic}")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafka_servers,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='cassandra-writer-group',
        value_deserializer=None  # On parse manuellement
    )
    logger.info("✓ Consumer Kafka connecté")
    
    logger.info("=" * 60)
    logger.info(f"📊 Traitement par batch de {batch_size} messages")
    logger.info("   Appuyez sur Ctrl+C pour arrêter")
    logger.info("=" * 60)
    
    messages_buffer = []
    total_written = 0
    batch_count = 0
    
    try:
        for message in consumer:
            messages_buffer.append(message)
            
            # Traiter quand le buffer atteint la taille souhaitée
            if len(messages_buffer) >= batch_size:
                batch_count += 1
                
                # Agréger les données
                aggregated = aggregate_delays(messages_buffer)
                
                # Écrire dans Cassandra
                count = write_to_cassandra(session, aggregated)
                total_written += count
                
                logger.info(f"✅ Batch {batch_count}: {count} aéroports mis à jour | Total: {total_written}")
                
                # Vider le buffer
                messages_buffer = []
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Arrêt du consumer...")
        
        # Traiter les messages restants
        if messages_buffer:
            aggregated = aggregate_delays(messages_buffer)
            count = write_to_cassandra(session, aggregated)
            total_written += count
            logger.info(f"✅ Messages restants traités: {count} aéroports")
        
        logger.info(f"📊 Total écrit: {total_written} mises à jour")
        
    finally:
        consumer.close()
        session.shutdown()
        cluster.shutdown()
        logger.info("✓ Connexions fermées")

if __name__ == "__main__":
    run_consumer()
