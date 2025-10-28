"""
Kafka Producer pour ingérer les données de vols depuis CSV vers Kafka
"""
from kafka import KafkaProducer
import pandas as pd
import json
import time
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_producer(bootstrap_servers='kafka:9092', max_retries=10):
    """Crée un producer Kafka avec retry logic"""
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_request_size=10485760,  # 10MB
                buffer_memory=33554432,  # 32MB
                compression_type='gzip'
            )
            logger.info("✓ Connexion à Kafka réussie")
            return producer
        except Exception as e:
            logger.warning(f"Tentative {attempt + 1}/{max_retries} - Erreur: {e}")
            time.sleep(5)
    
    raise Exception("Impossible de se connecter à Kafka")

def send_flights_to_kafka(csv_file, topic='live-flights', batch_size=100, delay=0.01):
    """
    Envoie les données de vols vers Kafka
    
    Args:
        csv_file: Chemin vers le fichier CSV
        topic: Nom du topic Kafka
        batch_size: Nombre de messages à envoyer avant flush
        delay: Délai entre les messages (en secondes)
    """
    try:
        # Connexion au producer
        producer = create_producer()
        
        # Lecture du CSV par chunks pour économiser la mémoire
        logger.info(f"📖 Lecture du fichier {csv_file}...")
        chunk_size = 10000
        total_sent = 0
        
        for chunk_idx, df_chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size)):
            logger.info(f"📦 Traitement du chunk {chunk_idx + 1} ({len(df_chunk)} lignes)...")
            
            for idx, row in df_chunk.iterrows():
                try:
                    # Conversion en dictionnaire et nettoyage des NaN
                    message = row.to_dict()
                    # Remplacer NaN par None pour JSON
                    message = {k: (None if pd.isna(v) else v) for k, v in message.items()}
                    
                    # Envoi vers Kafka
                    producer.send(topic, value=message)
                    total_sent += 1
                    
                    # Flush périodique
                    if total_sent % batch_size == 0:
                        producer.flush()
                        logger.info(f"✓ {total_sent} messages envoyés")
                    
                    # Délai pour éviter de surcharger
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du message {idx}: {e}")
                    continue
        
        # Flush final
        producer.flush()
        logger.info(f"✓ Terminé! Total de {total_sent} messages envoyés au topic '{topic}'")
        producer.close()
        
    except FileNotFoundError:
        logger.error(f"❌ Fichier non trouvé: {csv_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configuration
    CSV_FILE = "/data/2018.csv"  # Chemin dans le conteneur Docker
    TOPIC = "live-flights"
    
    # Paramètres personnalisables via arguments
    if len(sys.argv) > 1:
        CSV_FILE = sys.argv[1]
    if len(sys.argv) > 2:
        TOPIC = sys.argv[2]
    
    logger.info("=" * 60)
    logger.info("🚀 Démarrage du producteur Kafka pour données de vols")
    logger.info("=" * 60)
    logger.info(f"📁 Fichier: {CSV_FILE}")
    logger.info(f"📡 Topic: {TOPIC}")
    logger.info("=" * 60)
    
    send_flights_to_kafka(CSV_FILE, TOPIC)
