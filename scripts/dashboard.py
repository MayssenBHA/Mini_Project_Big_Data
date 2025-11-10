"""
Dashboard Streamlit pour Architecture Lambda - Big Data Flight Delays
Visualisation des données Batch Layer + Speed Layer
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cassandra.cluster import Cluster
from datetime import datetime
import time

# Configuration de la page
st.set_page_config(
    page_title="Lambda Architecture Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .layer-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .batch-layer {
        background-color: #3498db;
        color: white;
    }
    .speed-layer {
        background-color: #e74c3c;
        color: white;
    }
    .serving-layer {
        background-color: #9b59b6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache pour 5 minutes
def load_batch_data():
       """Charge les données du Batch Layer depuis Hive"""
    try:
        from pyspark.sql import SparkSession
        
        # Créer une session Spark avec support Hive
        spark = SparkSession.builder \
            .appName("DashboardBatchQuery") \
            .config("spark.sql.catalogImplementation", "hive") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-master:9000") \
            .config("spark.sql.warehouse.dir", "hdfs://hadoop-master:9000/user/hive/warehouse") \
            .enableHiveSupport() \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("ERROR")
        
        # Requête Hive pour récupérer les données batch
        query = """
            SELECT 
                origin,
                avg_delay,
                avg_dep_delay,
                total_flights,
                delayed_flights,
                avg_distance,
                avg_air_time,
                delay_rate
            FROM batch_views.airport_delay_stats
            ORDER BY avg_delay DESC
        """
        
        df_spark = spark.sql(query)
        df = df_spark.toPandas()
        
        spark.stop()
        
        df['source'] = 'Batch Layer'
        return df

@st.cache_data(ttl=30)  # Cache pour 30 secondes (données temps réel)
def load_speed_data():
    """Charge les données du Speed Layer depuis Cassandra"""
    try:
        cluster = Cluster(['cassandra'])
        session = cluster.connect('realtime')
        
        # Requête Cassandra
        query = "SELECT origin, recent_delay, recent_dep_delay FROM recent_delays"
        rows = session.execute(query)
        
        data = []
        for row in rows:
            if row.recent_delay is not None and row.recent_dep_delay is not None:
                data.append({
                    'origin': row.origin,
                    'avg_delay': float(row.recent_delay),
                    'avg_dep_delay': float(row.recent_dep_delay),
                    'source': 'Speed Layer'
                })
        
        session.shutdown()
        cluster.shutdown()
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"⚠️ Erreur connexion Cassandra: {e}")
        return pd.DataFrame()

def create_comparison_chart(batch_df, speed_df, airport_code):
    """Crée un graphique de comparaison Batch vs Speed pour un aéroport"""
    # Filtrer les données pour l'aéroport sélectionné
    batch_airport = batch_df[batch_df['origin'] == airport_code]
    speed_airport = speed_df[speed_df['origin'] == airport_code]
    
    if batch_airport.empty and speed_airport.empty:
        return None
    
    # Créer le graphique
    fig = go.Figure()
    
    # Batch Layer
    if not batch_airport.empty:
        fig.add_trace(go.Bar(
            name='Batch (Historique)',
            x=['Retard Arrivée', 'Retard Départ'],
            y=[batch_airport.iloc[0]['avg_delay'], batch_airport.iloc[0]['avg_dep_delay']],
            marker_color='#3498db',
            text=[f"{batch_airport.iloc[0]['avg_delay']:.1f} min", 
                  f"{batch_airport.iloc[0]['avg_dep_delay']:.1f} min"],
            textposition='auto',
        ))
    
    # Speed Layer
    if not speed_airport.empty:
        fig.add_trace(go.Bar(
            name='Speed (Temps Réel)',
            x=['Retard Arrivée', 'Retard Départ'],
            y=[speed_airport.iloc[0]['avg_delay'], speed_airport.iloc[0]['avg_dep_delay']],
            marker_color='#e74c3c',
            text=[f"{speed_airport.iloc[0]['avg_delay']:.1f} min", 
                  f"{speed_airport.iloc[0]['avg_dep_delay']:.1f} min"],
            textposition='auto',
        ))
    
    fig.update_layout(
        title=f"Comparaison Batch vs Speed - Aéroport {airport_code}",
        xaxis_title="Type de Retard",
        yaxis_title="Minutes de Retard",
        barmode='group',
        height=400
    )
    
    return fig

def main():
    """Fonction principale du dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">✈️ Lambda Architecture Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Analyse des Retards de Vols - Architecture Temps Réel & Batch</p>', unsafe_allow_html=True)
    
    # Badges des couches
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<span class="layer-badge batch-layer">🗄️ BATCH LAYER</span>', unsafe_allow_html=True)
        st.caption("7.2M vols analysés (2018)")
    with col2:
        st.markdown('<span class="layer-badge speed-layer">⚡ SPEED LAYER</span>', unsafe_allow_html=True)
        st.caption("Données temps réel")
    with col3:
        st.markdown('<span class="layer-badge serving-layer">🎯 SERVING LAYER</span>', unsafe_allow_html=True)
        st.caption("Vue combinée")
    
    st.markdown("---")
    
    # Chargement des données
    with st.spinner("📊 Chargement des données..."):
        batch_df = load_batch_data()
        speed_df = load_speed_data()
    
    # Sidebar - Filtres
    st.sidebar.header("🔍 Filtres")
    
    # Sélection de la vue
    view_mode = st.sidebar.radio(
        "Mode d'affichage",
        ["📊 Vue d'ensemble", "🔍 Recherche par aéroport", "📈 Comparaison Batch vs Speed"]
    )
    
    # Métrique d'auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.info("⏱️ Actualisation automatique activée")
        time.sleep(30)
        st.rerun()
    
    # Vue d'ensemble
    if view_mode == "📊 Vue d'ensemble":
        st.header("📊 Vue d'Ensemble - Statistiques Globales")
        
        # Métriques clés
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🗄️ Aéroports Batch",
                value="358",
                delta="Historique complet"
            )
        
        with col2:
            st.metric(
                label="⚡ Aéroports Speed",
                value=len(speed_df),
                delta="Temps réel"
            )
        
        with col3:
            st.metric(
                label="📦 Vols Analysés",
                value="7.2M",
                delta="Année 2018"
            )
        
        with col4:
            if not speed_df.empty:
                avg_realtime = speed_df['avg_delay'].mean()
                st.metric(
                    label="⏱️ Retard Moyen RT",
                    value=f"{avg_realtime:.1f} min",
                    delta=f"{avg_realtime - batch_df['avg_delay'].mean():.1f} min"
                )
        
        st.markdown("---")
        
        # Top 20 aéroports Batch Layer
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗄️ Top 20 Retards - Batch Layer (Historique)")
            fig_batch = px.bar(
                batch_df.head(20),
                x='origin',
                y='avg_delay',
                color='avg_delay',
                color_continuous_scale='Reds',
                labels={'origin': 'Aéroport', 'avg_delay': 'Retard Moyen (min)'},
                title="Retards Historiques (2018)"
            )
            fig_batch.update_layout(height=400)
            st.plotly_chart(fig_batch, use_container_width=True)
        
        with col2:
            st.subheader("⚡ Top 20 Retards - Speed Layer (Temps Réel)")
            if not speed_df.empty:
                speed_top = speed_df.nlargest(20, 'avg_delay')
                fig_speed = px.bar(
                    speed_top,
                    x='origin',
                    y='avg_delay',
                    color='avg_delay',
                    color_continuous_scale='Blues',
                    labels={'origin': 'Aéroport', 'avg_delay': 'Retard Moyen (min)'},
                    title="Retards Temps Réel"
                )
                fig_speed.update_layout(height=400)
                st.plotly_chart(fig_speed, use_container_width=True)
            else:
                st.info("⚠️ Aucune donnée temps réel disponible")
        
        # Tableau de données
        st.markdown("---")
        st.subheader("📋 Données Détaillées - Batch Layer")
        st.dataframe(
            batch_df.head(20).style.background_gradient(cmap='Reds', subset=['avg_delay', 'avg_dep_delay']),
            use_container_width=True
        )
    
    # Recherche par aéroport
    elif view_mode == "🔍 Recherche par aéroport":
        st.header("🔍 Recherche par Aéroport")
        
        # Sélection de l'aéroport
        all_airports = sorted(set(batch_df['origin'].tolist() + speed_df['origin'].tolist()))
        selected_airport = st.selectbox(
            "Sélectionnez un aéroport",
            all_airports,
            index=0
        )
        
        if selected_airport:
            col1, col2 = st.columns(2)
            
            # Batch Layer
            with col1:
                st.subheader(f"🗄️ Batch Layer - {selected_airport}")
                batch_airport = batch_df[batch_df['origin'] == selected_airport]
                if not batch_airport.empty:
                    st.metric("Retard Arrivée Moyen", f"{batch_airport.iloc[0]['avg_delay']:.1f} min")
                    st.metric("Retard Départ Moyen", f"{batch_airport.iloc[0]['avg_dep_delay']:.1f} min")
                    st.info("📊 Basé sur l'historique 2018 (7.2M vols)")
                else:
                    st.warning("Pas de données historiques pour cet aéroport")
            
            # Speed Layer
            with col2:
                st.subheader(f"⚡ Speed Layer - {selected_airport}")
                speed_airport = speed_df[speed_df['origin'] == selected_airport]
                if not speed_airport.empty:
                    st.metric("Retard Arrivée Actuel", f"{speed_airport.iloc[0]['avg_delay']:.1f} min")
                    st.metric("Retard Départ Actuel", f"{speed_airport.iloc[0]['avg_dep_delay']:.1f} min")
                    st.info("⚡ Données temps réel (Kafka → Cassandra)")
                else:
                    st.warning("Pas de données temps réel pour cet aéroport")
            
            # Graphique de comparaison
            st.markdown("---")
            fig = create_comparison_chart(batch_df, speed_df, selected_airport)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison Batch vs Speed
    elif view_mode == "📈 Comparaison Batch vs Speed":
        st.header("📈 Comparaison Batch Layer vs Speed Layer")
        
        # Aéroports communs
        if not speed_df.empty:
            common_airports = set(batch_df['origin']).intersection(set(speed_df['origin']))
            
            if common_airports:
                st.success(f"✅ {len(common_airports)} aéroports avec données Batch + Speed")
                
                # Merge des données
                merged_df = pd.merge(
                    batch_df[['origin', 'avg_delay', 'avg_dep_delay']].rename(columns={
                        'avg_delay': 'batch_delay',
                        'avg_dep_delay': 'batch_dep_delay'
                    }),
                    speed_df[['origin', 'avg_delay', 'avg_dep_delay']].rename(columns={
                        'avg_delay': 'speed_delay',
                        'avg_dep_delay': 'speed_dep_delay'
                    }),
                    on='origin',
                    how='inner'
                )
                
                # Calculer les différences
                merged_df['diff_delay'] = merged_df['speed_delay'] - merged_df['batch_delay']
                merged_df['diff_dep_delay'] = merged_df['speed_dep_delay'] - merged_df['batch_dep_delay']
                
                # Graphique scatter
                fig = px.scatter(
                    merged_df,
                    x='batch_delay',
                    y='speed_delay',
                    text='origin',
                    labels={
                        'batch_delay': 'Retard Batch (Historique)',
                        'speed_delay': 'Retard Speed (Temps Réel)'
                    },
                    title='Corrélation Batch vs Speed - Retards d\'Arrivée',
                    color='diff_delay',
                    color_continuous_scale='RdYlGn_r'
                )
                
                # Ligne de référence (x=y)
                fig.add_trace(go.Scatter(
                    x=[merged_df['batch_delay'].min(), merged_df['batch_delay'].max()],
                    y=[merged_df['batch_delay'].min(), merged_df['batch_delay'].max()],
                    mode='lines',
                    name='Référence (Batch = Speed)',
                    line=dict(dash='dash', color='gray')
                ))
                
                fig.update_traces(textposition='top center')
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top différences
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 Top 10 - Retards Augmentés (Speed > Batch)")
                    top_increased = merged_df.nlargest(10, 'diff_delay')[['origin', 'batch_delay', 'speed_delay', 'diff_delay']]
                    st.dataframe(
                        top_increased.style.format({
                            'batch_delay': '{:.1f} min',
                            'speed_delay': '{:.1f} min',
                            'diff_delay': '{:+.1f} min'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    st.subheader("📉 Top 10 - Retards Diminués (Speed < Batch)")
                    top_decreased = merged_df.nsmallest(10, 'diff_delay')[['origin', 'batch_delay', 'speed_delay', 'diff_delay']]
                    st.dataframe(
                        top_decreased.style.format({
                            'batch_delay': '{:.1f} min',
                            'speed_delay': '{:.1f} min',
                            'diff_delay': '{:+.1f} min'
                        }),
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ Aucun aéroport commun entre Batch et Speed")
        else:
            st.error("❌ Pas de données Speed Layer disponibles")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🚀 <b>Lambda Architecture</b> - Big Data Flight Delays Analysis</p>
        <p>Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>🗄️ Batch: 7,213,446 vols | ⚡ Speed: {len(speed_df)} aéroports | 🎯 Serving: Vue combinée</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
