import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Classificação Tecnológica - Biogás SP",
    page_icon="🔬",
    layout="wide"
)

# CSS personalizado - versão minimalista
st.markdown("""
<style>
    .main-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin-bottom: 1rem;
    }
    .tech-card {
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        background: #ffffff;
        font-size: 0.9rem;
    }
    .no-plant-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 4px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h2>🔬 Classificação de Biogás SP</h2>
    <p>Prof. Bruna Moraes - NIPE-CP2B UNICAMP</p>
</div>
""", unsafe_allow_html=True)

# Inicializar session state
if 'plant_index' not in st.session_state:
    st.session_state.plant_index = 0
if 'classifications' not in st.session_state:
    st.session_state.classifications = {}

# Função para carregar dados
@st.cache_data
def load_plant_data():
    """Carrega dados das plantas de biogás"""
    try:
        # Substitua pelo caminho do seu CSV baixado do GEE
        df = pd.read_csv('Plantas_Biogas_Para_Classificacao.csv')
        return df
    except FileNotFoundError:
        st.error("❌ Arquivo 'Plantas_Biogas_Para_Classificacao.csv' não encontrado!")
        st.info("📥 Baixe o arquivo do Google Drive e coloque na mesma pasta do script.")
        return None

def save_classification(plant_id, classification_data):
    """Salva classificação no session state e arquivo"""
    st.session_state.classifications[plant_id] = classification_data
    
    # Salvar em arquivo JSON para backup
    with open('classificacoes_biogas.json', 'w') as f:
        json.dump(st.session_state.classifications, f, indent=2)

def create_satellite_map(lat, lon, municipio):
    """Cria mapa de satélite interativo"""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=18,
        tiles=None
    )
    
    # Adicionar diferentes tipos de imagem
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='ESRI World Imagery',
        name='Satélite ESRI',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satélite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Marker da planta
    folium.Marker(
        [lat, lon],
        popup=f"<b>{municipio}</b><br>Planta de Biogás<br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
        icon=folium.Icon(color='red', icon='industry', prefix='fa')
    ).add_to(m)
    
    # Círculos para escala de referência
    folium.Circle(
        [lat, lon], radius=100, color='yellow', weight=2, opacity=0.8,
        popup='100m de raio'
    ).add_to(m)
    
    folium.Circle(
        [lat, lon], radius=500, color='orange', weight=2, opacity=0.6,
        popup='500m de raio'
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    return m

# Carregar dados
df_plantas = load_plant_data()

if df_plantas is not None:
    total_plantas = len(df_plantas)
    
    # Sidebar - Navegação
    with st.sidebar:
        st.header("🎯 NAVEGAÇÃO")
        
        # Seletor de planta
        current_plant = st.selectbox(
            "Selecionar Planta:",
            range(total_plantas),
            index=st.session_state.plant_index,
            format_func=lambda x: f"{x+1}. {df_plantas.iloc[x]['Municipio']}"
        )
        st.session_state.plant_index = current_plant
        
        # Botões de navegação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Anterior") and current_plant > 0:
                st.session_state.plant_index = current_plant - 1
                st.rerun()
        with col2:
            if st.button("Próxima ➡️") and current_plant < total_plantas - 1:
                st.session_state.plant_index = current_plant + 1
                st.rerun()
        
        # Progresso simplificado
        st.markdown("### 📊 Progresso")
        classified_count = len(st.session_state.classifications)
        progress = classified_count / total_plantas
        st.progress(progress)
        st.write(f"{classified_count}/{total_plantas} plantas ({progress:.0%})")

        # Estatísticas compactas
        if classified_count > 0:
            techs = [v['tecnologia'] for v in st.session_state.classifications.values()]
            stats_text = []
            for tech in ['BAIXA', 'MEDIA', 'ALTA', 'SEM_PLANTA']:
                count = techs.count(tech)
                if count > 0:
                    stats_text.append(f"{tech}: {count}")
            if stats_text:
                st.write(" | ".join(stats_text))
    
    # Dados da planta atual
    planta = df_plantas.iloc[current_plant]
    plant_id = f"plant_{current_plant:03d}"
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📍 {current_plant + 1}/{total_plantas} - {planta['Municipio']}")

        # Informações compactas da planta
        st.write(f"**Coordenadas:** {planta['Latitude']:.4f}, {planta['Longitude']:.4f}")

        if 'cana_ha' in planta:
            st.write(f"**Cana:** {planta['cana_ha']:.0f} ha")

        # Mapa de satélite
        st.markdown("### 🛰️ Imagem de Satélite")
        satellite_map = create_satellite_map(
            planta['Latitude'], 
            planta['Longitude'], 
            planta['Municipio']
        )
        
        map_data = st_folium(
            satellite_map, 
            height=500, 
            width=None,
            returned_objects=["last_object_clicked"]
        )
        
        # Link direto para Google Maps
        gmaps_url = f"https://www.google.com/maps/@{planta['Latitude']},{planta['Longitude']},18z"
        st.markdown(f"🔗 [Abrir no Google Maps]({gmaps_url})")
    
    with col2:
        st.subheader("🎯 CLASSIFICAÇÃO")
        
        # Guia de classificação simplificado
        st.markdown("### 🎯 Guia de Classificação")

        st.markdown("""
        <div class="tech-card">
            <strong>🔴 BAIXA:</strong> Lagoas grandes (>2000m²), formato irregular
        </div>
        <div class="tech-card">
            <strong>🟡 MÉDIA:</strong> Tanques/CRTs (200-2000m²), estruturas cilíndricas
        </div>
        <div class="tech-card">
            <strong>🟢 ALTA:</strong> Cúpulas compactas (<200m²), alta tecnologia
        </div>
        <div class="no-plant-warning">
            <strong>⚠️ SEM PLANTA:</strong> Use quando não há planta de biogás visível na localização
        </div>
        """, unsafe_allow_html=True)
        
        # Formulário de classificação
        with st.form(f"classification_form_{plant_id}"):
            tecnologia = st.radio(
                "**Classificação:**",
                ["BAIXA", "MEDIA", "ALTA", "SEM_PLANTA"],
                help="SEM_PLANTA = não há planta de biogás visível nesta localização"
            )
            
            confianca = st.slider("**Confiança (%):**", 50, 100, 80)

            observacoes = st.text_area(
                "**Observações:**",
                placeholder="Descreva o que vê na imagem de satélite...",
                height=80
            )
            
            submitted = st.form_submit_button(
                "✅ SALVAR CLASSIFICAÇÃO",
                type="primary"
            )
            
            if submitted:
                classification_data = {
                    'plant_index': current_plant,
                    'municipio': planta['Municipio'],
                    'latitude': planta['Latitude'],
                    'longitude': planta['Longitude'],
                    'tecnologia': tecnologia,
                    'confianca': confianca,
                    'observacoes': observacoes,
                    'timestamp': datetime.now().isoformat()
                }
                
                save_classification(plant_id, classification_data)
                st.success(f"✅ Planta {current_plant + 1} classificada como {tecnologia}!")
                
                # Auto-avançar para próxima planta
                if current_plant < total_plantas - 1:
                    st.session_state.plant_index = current_plant + 1
                    st.rerun()
        
        # Mostrar classificação atual se existir
        if plant_id in st.session_state.classifications:
            current_class = st.session_state.classifications[plant_id]
            st.info(f"**Classificação atual:** {current_class['tecnologia']} ({current_class['confianca']}%)")
    
    # Download dos resultados
    if st.session_state.classifications:
        st.subheader("💾 EXPORTAR RESULTADOS")
        
        # Converter para DataFrame
        results_df = pd.DataFrame(list(st.session_state.classifications.values()))
        
        # Botão de download
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Classificações (CSV)",
            data=csv_data,
            file_name=f"classificacoes_biogas_sp_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Resumo estatístico
        if len(results_df) > 0:
            st.subheader("📊 RESUMO ESTATÍSTICO")
            tech_counts = results_df['tecnologia'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("BAIXA", tech_counts.get('BAIXA', 0))
            with col2:
                st.metric("MÉDIA", tech_counts.get('MEDIA', 0))
            with col3:
                st.metric("ALTA", tech_counts.get('ALTA', 0))
            with col4:
                st.metric("SEM PLANTA", tech_counts.get('SEM_PLANTA', 0))
            
            st.write(f"**Confiança média:** {results_df['confianca'].mean():.1f}%")

else:
    st.error("❌ Não foi possível carregar os dados das plantas!")
    st.info("📋 Certifique-se de que o arquivo 'Plantas_Biogas_Para_Classificacao.csv' está na pasta do script.")
