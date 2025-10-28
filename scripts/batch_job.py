"""
Batch Layer - Traitement batch avec Spark pour calculer les retards moyens par aéroport
Crée une vue batch dans Hive pour analyse historique
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, sum, col, when
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_spark_session():
    """Crée une session Spark avec configuration pour HDFS et Hive"""
    return SparkSession.builder \
        .appName("FlightDelayBatchProcessing") \
        .master("spark://spark-master:7077") \
        .config("spark.sql.warehouse.dir", "hdfs://hadoop-master:9000/user/hive/warehouse") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-master:9000") \
        .config("spark.sql.catalogImplementation", "hive") \
        .enableHiveSupport() \
        .getOrCreate()

def process_batch_data(spark, hdfs_path):
    """
    Traite les données de vols en batch et calcule les statistiques par aéroport
    
    Args:
        spark: SparkSession
        hdfs_path: Chemin HDFS vers les données CSV
    """
    logger.info(f"📖 Lecture des données depuis {hdfs_path}...")
    
    # Lecture des données CSV depuis HDFS
    df = spark.read.csv(
        hdfs_path,
        header=True,
        inferSchema=True,
        mode="DROPMALFORMED"  # Ignore les lignes mal formées
    )
    
    logger.info(f"✓ {df.count()} lignes chargées")
    
    # Affichage du schéma
    logger.info("📋 Schéma des données:")
    df.printSchema()
    
    # Nettoyage: Filtrer les vols annulés et les valeurs nulles
    df_clean = df.filter(
        (col("CANCELLED") == 0) & 
        (col("ARR_DELAY").isNotNull()) &
        (col("ORIGIN").isNotNull())
    )
    
    logger.info(f"✓ {df_clean.count()} lignes après nettoyage")
    
    # Calcul des statistiques par aéroport d'origine
    logger.info("📊 Calcul des statistiques par aéroport...")
    
    batch_view = df_clean.groupBy("ORIGIN").agg(
        avg("ARR_DELAY").alias("avg_delay"),
        avg("DEP_DELAY").alias("avg_dep_delay"),
        count("*").alias("total_flights"),
        sum(when(col("ARR_DELAY") > 15, 1).otherwise(0)).alias("delayed_flights"),
        avg("DISTANCE").alias("avg_distance"),
        avg("AIR_TIME").alias("avg_air_time")
    )
    
    # Calcul du taux de retard
    batch_view = batch_view.withColumn(
        "delay_rate",
        (col("delayed_flights") / col("total_flights")) * 100
    )
    
    # Tri par retard moyen décroissant
    batch_view = batch_view.orderBy(col("avg_delay").desc())
    
    logger.info("✓ Statistiques calculées")
    
    # Affichage des 20 premiers aéroports
    logger.info("\n📊 Top 20 aéroports avec le plus de retards:")
    batch_view.show(20, truncate=False)
    
    return batch_view

def save_to_hive(df, database="batch_views", table="airport_delay_stats"):
    """
    Sauvegarde les résultats dans Hive
    
    Args:
        df: DataFrame Spark
        database: Nom de la base de données Hive
        table: Nom de la table Hive
    """
    logger.info(f"💾 Sauvegarde dans Hive: {database}.{table}...")
    
    # Création de la base de données si elle n'existe pas
    df.sparkSession.sql(f"CREATE DATABASE IF NOT EXISTS {database}")
    
    # Sauvegarde en mode overwrite
    df.write \
        .mode("overwrite") \
        .format("hive") \
        .saveAsTable(f"{database}.{table}")
    
    logger.info(f"✓ Données sauvegardées dans {database}.{table}")
    
    # Vérification
    result_count = df.sparkSession.sql(f"SELECT COUNT(*) as count FROM {database}.{table}").collect()[0]['count']
    logger.info(f"✓ {result_count} aéroports dans la table")

def run_batch_job(hdfs_input_path="/data/flights_raw/*.csv"):
    """
    Exécute le job batch complet
    
    Args:
        hdfs_input_path: Chemin HDFS vers les fichiers CSV d'entrée
    """
    try:
        logger.info("=" * 60)
        logger.info("🚀 Démarrage du Batch Layer (Architecture Lambda)")
        logger.info("=" * 60)
        
        # Création de la session Spark
        spark = create_spark_session()
        spark.sparkContext.setLogLevel("WARN")
        
        # Traitement des données
        batch_view = process_batch_data(spark, hdfs_input_path)
        
        # Sauvegarde dans Hive
        save_to_hive(batch_view)
        
        logger.info("=" * 60)
        logger.info("✅ Batch job terminé avec succès!")
        logger.info("=" * 60)
        logger.info("📌 Pour requêter les données:")
        logger.info("   docker exec -it hive beeline -u jdbc:hive2://localhost:10000")
        logger.info("   SELECT * FROM batch_views.airport_delay_stats LIMIT 10;")
        logger.info("=" * 60)
        
        spark.stop()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du batch job: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Chemin HDFS personnalisable via argument
    hdfs_path = "/data/flights_raw/*.csv"
    
    if len(sys.argv) > 1:
        hdfs_path = sys.argv[1]
    
    run_batch_job(hdfs_path)
