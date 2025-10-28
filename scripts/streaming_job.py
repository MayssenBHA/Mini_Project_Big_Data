"""
Speed Layer - Traitement en temps réel avec Spark Structured Streaming
Consomme depuis Kafka et écrit dans Cassandra pour les vues temps réel
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, window, current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType, StringType, TimestampType
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_flight_schema():
    """
    Définit le schéma des données de vols
    Basé sur le dataset Kaggle des vols US (colonnes en majuscules)
    """
    return StructType([
        StructField("FL_DATE", StringType(), True),
        StructField("OP_CARRIER", StringType(), True),
        StructField("OP_CARRIER_FL_NUM", IntegerType(), True),
        StructField("ORIGIN", StringType(), True),
        StructField("DEST", StringType(), True),
        StructField("CRS_DEP_TIME", IntegerType(), True),
        StructField("DEP_TIME", DoubleType(), True),
        StructField("DEP_DELAY", DoubleType(), True),
        StructField("TAXI_OUT", DoubleType(), True),
        StructField("WHEELS_OFF", DoubleType(), True),
        StructField("WHEELS_ON", DoubleType(), True),
        StructField("TAXI_IN", DoubleType(), True),
        StructField("CRS_ARR_TIME", IntegerType(), True),
        StructField("ARR_TIME", DoubleType(), True),
        StructField("ARR_DELAY", DoubleType(), True),
        StructField("CANCELLED", DoubleType(), True),
        StructField("CANCELLATION_CODE", StringType(), True),
        StructField("DIVERTED", DoubleType(), True),
        StructField("CRS_ELAPSED_TIME", DoubleType(), True),
        StructField("ACTUAL_ELAPSED_TIME", DoubleType(), True),
        StructField("AIR_TIME", DoubleType(), True),
        StructField("DISTANCE", DoubleType(), True),
        StructField("CARRIER_DELAY", DoubleType(), True),
        StructField("WEATHER_DELAY", DoubleType(), True),
        StructField("NAS_DELAY", DoubleType(), True),
        StructField("SECURITY_DELAY", DoubleType(), True),
        StructField("LATE_AIRCRAFT_DELAY", DoubleType(), True)
    ])

def create_spark_session():
    """Crée une session Spark avec support Kafka et Cassandra"""
    return SparkSession.builder \
        .appName("FlightDelayStreamProcessing") \
        .master("spark://spark-master:7077") \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint") \
        .getOrCreate()

def process_kafka_stream(spark, kafka_servers="kafka:9092", topic="live-flights"):
    """
    Lit le stream depuis Kafka et traite les données de vols en temps réel
    
    Args:
        spark: SparkSession
        kafka_servers: Adresse du serveur Kafka
        topic: Topic Kafka à consommer
    """
    logger.info(f"📡 Connexion à Kafka: {kafka_servers}, topic: {topic}...")
    
    # Lecture du stream Kafka
    kafka_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    logger.info("✓ Stream Kafka connecté")
    
    # Parse JSON avec schéma
    flight_schema = get_flight_schema()
    
    flights_df = kafka_stream.select(
        from_json(col("value").cast("string"), flight_schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select("data.*", "kafka_timestamp")
    
    # Filtrage des vols valides (non annulés)
    flights_df = flights_df.filter(
        (col("CANCELLED") == 0) & 
        (col("ARR_DELAY").isNotNull()) &
        (col("ORIGIN").isNotNull())
    )
    
    logger.info("✓ Stream parsé et filtré")
    
    return flights_df

def compute_realtime_metrics(flights_df):
    """
    Calcule les métriques en temps réel par aéroport
    Utilise des fenêtres temporelles pour agréger les données récentes
    
    Args:
        flights_df: DataFrame du stream de vols
    """
    logger.info("📊 Calcul des métriques temps réel...")
    
    # Agrégation par aéroport d'origine sans fenêtre temporelle
    # (car nous n'avons pas de vraie timestamp dans les données historiques)
    realtime_stats = flights_df.groupBy("ORIGIN").agg(
        avg("ARR_DELAY").alias("recent_delay"),
        avg("DEP_DELAY").alias("recent_dep_delay")
    )
    
    # Sélection des colonnes finales
    realtime_stats = realtime_stats.select(
        col("ORIGIN").alias("origin"),
        col("recent_delay"),
        col("recent_dep_delay")
    )
    
    return realtime_stats

def write_to_cassandra(stream_df, keyspace="realtime", table="recent_delays"):
    """
    Écrit le stream vers Cassandra
    
    Args:
        stream_df: DataFrame du stream
        keyspace: Keyspace Cassandra
        table: Table Cassandra
    """
    logger.info(f"💾 Configuration de l'écriture vers Cassandra: {keyspace}.{table}...")
    
    query = stream_df.writeStream \
        .outputMode("update") \
        .format("org.apache.spark.sql.cassandra") \
        .option("keyspace", keyspace) \
        .option("table", table) \
        .option("checkpointLocation", f"/tmp/checkpoint_{table}") \
        .start()
    
    logger.info("✓ Stream vers Cassandra démarré")
    
    return query

def write_to_console(stream_df):
    """
    Écrit le stream vers la console pour debug
    
    Args:
        stream_df: DataFrame du stream
    """
    logger.info("🖥️  Configuration de l'écriture vers la console...")
    
    query = stream_df.writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .start()
    
    logger.info("✓ Stream vers console démarré")
    
    return query

def run_streaming_job(kafka_servers="kafka:9092", topic="live-flights", output_mode="cassandra"):
    """
    Exécute le job de streaming complet
    
    Args:
        kafka_servers: Serveurs Kafka
        topic: Topic Kafka
        output_mode: 'cassandra' ou 'console'
    """
    try:
        logger.info("=" * 60)
        logger.info("🚀 Démarrage du Speed Layer (Architecture Lambda)")
        logger.info("=" * 60)
        
        # Création de la session Spark
        spark = create_spark_session()
        spark.sparkContext.setLogLevel("WARN")
        
        # Lecture et traitement du stream Kafka
        flights_stream = process_kafka_stream(spark, kafka_servers, topic)
        
        # Calcul des métriques temps réel
        realtime_metrics = compute_realtime_metrics(flights_stream)
        
        # Écriture vers la destination
        if output_mode == "cassandra":
            query = write_to_cassandra(realtime_metrics)
        else:
            query = write_to_console(realtime_metrics)
        
        logger.info("=" * 60)
        logger.info("✅ Streaming job démarré avec succès!")
        logger.info("=" * 60)
        logger.info("📊 Le job continue à traiter les données en temps réel...")
        logger.info("   Appuyez sur Ctrl+C pour arrêter")
        logger.info("=" * 60)
        
        # Attendre la terminaison
        query.awaitTermination()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Arrêt du streaming job...")
        spark.stop()
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du streaming job: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Configuration personnalisable via arguments
    kafka_servers = "kafka:9092"
    topic = "live-flights"
    output_mode = "console"  # Par défaut console pour debug
    
    if len(sys.argv) > 1:
        output_mode = sys.argv[1]  # 'cassandra' ou 'console'
    if len(sys.argv) > 2:
        topic = sys.argv[2]
    if len(sys.argv) > 3:
        kafka_servers = sys.argv[3]
    
    run_streaming_job(kafka_servers, topic, output_mode)
