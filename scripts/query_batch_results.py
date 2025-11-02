"""
Script pour requêter les résultats du Batch Layer
Alternative à Hive - Lit directement les fichiers Parquet depuis HDFS
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc, asc
import sys

def create_spark_session():
    """Crée une session Spark"""
    return SparkSession.builder \
        .appName("QueryBatchResults") \
        .master("spark://spark-master:7077") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-master:9000") \
        .getOrCreate()

def query_batch_data(spark, query_type="top_delays", limit=20):
    """
    Requête les données du Batch Layer
    
    Args:
        spark: SparkSession
        query_type: Type de requête ('top_delays', 'by_airport', 'stats')
        limit: Nombre de résultats
    """
    print("=" * 70)
    print("📊 BATCH LAYER - Requête des Données Historiques")
    print("=" * 70)
    
    # Lire les données depuis HDFS
    try:
        # Essayer de lire depuis le warehouse Hive (format CSV)
        df = spark.read.csv(
            "hdfs://hadoop-master:9000/user/hive/warehouse/batch_views.db/airport_delay_stats",
            header=False,
            inferSchema=True
        )
        # Nommer les colonnes manuellement
        df = df.toDF("origin", "avg_delay", "avg_dep_delay", "total_flights", "avg_distance", "avg_air_time")
        print(f"✓ Données chargées: {df.count()} aéroports")
    except Exception as e:
        print(f"❌ Erreur lecture depuis HDFS: {e}")
        raise
    
    print("\n" + "=" * 70)
    
    if query_type == "top_delays":
        print(f"🔴 TOP {limit} AÉROPORTS AVEC PLUS DE RETARDS (Moyenne)")
        print("=" * 70)
        result = df.orderBy(desc("avg_delay")).limit(limit)
        result.select(
            col("origin"),
            col("total_flights"),
            col("avg_delay").cast("int").alias("retard_moy_min"),
            col("avg_dep_delay").cast("int").alias("retard_dep_moy_min")
        ).show(limit, truncate=False)
        
    elif query_type == "low_delays":
        print(f"🟢 TOP {limit} AÉROPORTS AVEC MOINS DE RETARDS (Moyenne)")
        print("=" * 70)
        result = df.orderBy(asc("avg_delay")).limit(limit)
        result.select(
            col("origin"),
            col("total_flights"),
            col("avg_delay").cast("int").alias("retard_moy_min"),
            col("avg_dep_delay").cast("int").alias("retard_dep_moy_min")
        ).show(limit, truncate=False)
        
    elif query_type == "by_airport":
        # Recherche par code aéroport
        airport_code = sys.argv[2] if len(sys.argv) > 2 else "JFK"
        print(f"🔍 STATISTIQUES POUR L'AÉROPORT: {airport_code}")
        print("=" * 70)
        result = df.filter(col("origin") == airport_code)
        if result.count() > 0:
            result.show(truncate=False)
        else:
            print(f"❌ Aucune donnée pour l'aéroport {airport_code}")
    
    elif query_type == "stats":
        print("📈 STATISTIQUES GLOBALES DU BATCH LAYER")
        print("=" * 70)
        
        total_airports = df.count()
        total_flights = df.agg({"total_flights": "sum"}).collect()[0][0]
        avg_delay_all = df.agg({"avg_delay": "avg"}).collect()[0][0]
        
        print(f"\n✈️  Nombre total d'aéroports analysés: {total_airports}")
        print(f"✈️  Nombre total de vols: {int(total_flights):,}")
        print(f"⏱️  Retard moyen global: {avg_delay_all:.2f} minutes")
        
        print("\n📊 Distribution des retards:")
        df.select("avg_delay").describe().show()
        
        print("\n🏆 Top 10 aéroports les plus fréquentés:")
        df.orderBy(desc("total_flights")).limit(10).select(
            col("origin"),
            col("total_flights").alias("nb_vols"),
            col("avg_delay").cast("int").alias("retard_moy")
        ).show(10, truncate=False)
    
    else:
        print(f"❌ Type de requête inconnu: {query_type}")
        print("Types disponibles: top_delays, low_delays, by_airport, stats")
    
    print("\n" + "=" * 70)

def main():
    """Fonction principale"""
    query_type = sys.argv[1] if len(sys.argv) > 1 else "top_delays"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        query_batch_data(spark, query_type, limit)
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 QUERY BATCH RESULTS - Alternative à Hive")
    print("=" * 70)
    print("Usage:")
    print("  python query_batch_results.py [query_type] [airport_code] [limit]")
    print("\nTypes de requêtes:")
    print("  - top_delays   : Top aéroports avec plus de retards")
    print("  - low_delays   : Top aéroports avec moins de retards")
    print("  - by_airport   : Stats pour un aéroport spécifique (ex: JFK)")
    print("  - stats        : Statistiques globales")
    print("=" * 70 + "\n")
    
    main()
