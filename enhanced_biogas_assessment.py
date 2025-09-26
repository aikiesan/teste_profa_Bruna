import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import os
from datetime import datetime
import uuid
from folium.plugins import Draw, MeasureControl
import math

# Configuração da página
st.set_page_config(
    page_title="Avaliação de Plantas de Biogás - Prof. Bruna Moraes",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para design profissional
st.markdown("""
<style>
    /* Design profissional e moderno */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 600;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    .assessment-card {
        background: white;
        border: 2px solid #e1e5e9;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    .assessment-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .tech-indicator {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }

    .tech-indicator:hover {
        background: #e9ecef;
        border-color: #adb5bd;
    }

    .tech-pools { border-left: 4px solid #dc3545; }
    .tech-tanks { border-left: 4px solid #fd7e14; }
    .tech-biogas { border-left: 4px solid #28a745; }
    .tech-none { border-left: 4px solid #6c757d; }

    .coord-display {
        background: #e3f2fd;
        border: 1px solid #90caf9;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.9rem;
    }

    .progress-section {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .stat-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .certainty-high { background-color: #d4edda; border-color: #c3e6cb; }
    .certainty-medium { background-color: #fff3cd; border-color: #ffeaa7; }
    .certainty-low { background-color: #f8d7da; border-color: #f5c6cb; }

    .validation-panel {
        background: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .sidebar .element-container {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏭 Avaliação de Tecnologias de Biogás</h1>
    <p>Sistema de Classificação para Treinamento de Algoritmos ML com Imagens Sentinel</p>
    <p><strong>Prof. Bruna Moraes - NIPE-CP2B UNICAMP</strong></p>
</div>
""", unsafe_allow_html=True)

# Inicializar session state
if 'plant_index' not in st.session_state:
    st.session_state.plant_index = 0
if 'assessments' not in st.session_state:
    st.session_state.assessments = {}
if 'technology_coordinates' not in st.session_state:
    st.session_state.technology_coordinates = {}
if 'validation_data' not in st.session_state:
    st.session_state.validation_data = {}

# Funções utilitárias
@st.cache_data
def load_plant_data():
    """Carrega dados das plantas de biogás"""
    try:
        df = pd.read_csv('Plantas_Biogas_Para_Classificacao.csv')
        return df
    except FileNotFoundError:
        st.error("❌ Arquivo 'Plantas_Biogas_Para_Classificacao.csv' não encontrado!")
        st.info("📥 Coloque o arquivo CSV na mesma pasta do script.")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcula distância entre dois pontos em metros"""
    R = 6371000  # Raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi/2) * math.sin(delta_phi/2) +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def save_assessment(plant_id, assessment_data):
    """Salva avaliação completa e exporta CSV automaticamente"""
    st.session_state.assessments[plant_id] = assessment_data

    # Backup em arquivo JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    backup_file = f'biogas_assessments_backup_{timestamp}.json'

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump({
            'assessments': st.session_state.assessments,
            'coordinates': st.session_state.technology_coordinates,
            'validations': st.session_state.validation_data
        }, f, indent=2, ensure_ascii=False)

    # Exportar CSV automaticamente após cada avaliação
    csv_data = export_ml_training_data()
    if csv_data is not None:
        csv_filename = f'biogas_assessments_{timestamp}.csv'
        csv_data.to_csv(csv_filename, index=False, encoding='utf-8')
        return csv_filename
    return None

def create_assessment_map(lat, lon, municipio, existing_coords=None):
    """Cria mapa interativo para avaliação"""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=19,  # Increased zoom for better detail
        tiles=None,
        prefer_canvas=True  # Better performance
    )

    # High-quality satellite layer - Google Satellite only
    folium.TileLayer(
        'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='🌍 Google Satélite (HD)',
        overlay=False,
        control=False,  # No layer control needed for single layer
        max_zoom=22,
        subdomains=['mt0', 'mt1', 'mt2', 'mt3']
    ).add_to(m)

    # Marker da planta principal
    folium.Marker(
        [lat, lon],
        popup=f"""
        <div style='width:200px'>
            <h4>{municipio}</h4>
            <p><b>Localização Base</b></p>
            <p>Lat: {lat:.6f}</p>
            <p>Lon: {lon:.6f}</p>
        </div>
        """,
        icon=folium.Icon(color='blue', icon='industry', prefix='fa'),
        tooltip="📍 Localização da Planta"
    ).add_to(m)

    # Círculos de referência para escala
    folium.Circle(
        [lat, lon],
        radius=50,
        color='yellow',
        weight=2,
        opacity=0.7,
        fillOpacity=0.1,
        popup='Raio: 50m'
    ).add_to(m)

    folium.Circle(
        [lat, lon],
        radius=200,
        color='orange',
        weight=2,
        opacity=0.6,
        fillOpacity=0.05,
        popup='Raio: 200m'
    ).add_to(m)

    folium.Circle(
        [lat, lon],
        radius=500,
        color='red',
        weight=1,
        opacity=0.5,
        fillOpacity=0.02,
        popup='Raio: 500m'
    ).add_to(m)

    # Adicionar coordenadas de tecnologias existentes
    if existing_coords:
        colors = {'lagoas': 'red', 'biotanques': 'orange', 'alta_tech': 'green', 'outros': 'purple'}
        icons = {'lagoas': 'tint', 'biotanques': 'cog', 'alta_tech': 'star', 'outros': 'question'}

        for i, coord in enumerate(existing_coords):
            tech_type = coord.get('type', 'outros')
            folium.Marker(
                [coord['lat'], coord['lon']],
                popup=f"""
                <div style='width:180px'>
                    <h5>Tecnologia {i+1}</h5>
                    <p><b>Tipo:</b> {tech_type.replace('_', ' ').title()}</p>
                    <p><b>Coordenadas:</b></p>
                    <p>Lat: {coord['lat']:.6f}</p>
                    <p>Lon: {coord['lon']:.6f}</p>
                    <p><b>Observações:</b> {coord.get('notes', 'N/A')}</p>
                </div>
                """,
                icon=folium.Icon(
                    color=colors.get(tech_type, 'gray'),
                    icon=icons.get(tech_type, 'question'),
                    prefix='fa'
                ),
                tooltip=f"🔧 {tech_type.replace('_', ' ').title()}"
            ).add_to(m)

    # Ferramenta de medição
    MeasureControl(
        primary_length_unit='meters',
        secondary_length_unit='kilometers',
        primary_area_unit='sqmeters',
        secondary_area_unit='hectares'
    ).add_to(m)

    # Ferramenta de desenho
    Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': True,
            'polygon': True,
            'circle': True,
            'rectangle': True,
            'marker': True,
            'circlemarker': False,
        }
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m

def export_ml_training_data():
    """Exporta dados estruturados para treinamento ML"""
    if not st.session_state.assessments:
        return None

    ml_data = []

    for plant_id, assessment in st.session_state.assessments.items():
        base_record = {
            'plant_id': plant_id,
            'municipio': assessment['municipio'],
            'base_latitude': assessment['latitude'],
            'base_longitude': assessment['longitude'],
            'has_biogas_plant': assessment.get('has_plant', True),
            'overall_technology_level': assessment.get('tech_level', 'UNKNOWN'),
            'assessor_confidence': assessment.get('confidence', 0),
            'assessment_date': assessment.get('timestamp', ''),
            'validation_status': assessment.get('validation_status', 'PENDING'),
            'validation_confidence': assessment.get('validation_confidence', 0),
            'general_observations': assessment.get('observations', '')
        }

        # Coordenadas de tecnologias específicas
        tech_coords = st.session_state.technology_coordinates.get(plant_id, [])

        if tech_coords:
            for i, coord in enumerate(tech_coords):
                record = base_record.copy()
                record.update({
                    'technology_id': f"{plant_id}_tech_{i+1}",
                    'tech_latitude': coord['lat'],
                    'tech_longitude': coord['lon'],
                    'technology_type': coord.get('type', 'unknown'),
                    'estimated_area_m2': coord.get('area', 0),
                    'distance_from_base_m': calculate_distance(
                        base_record['base_latitude'],
                        base_record['base_longitude'],
                        coord['lat'],
                        coord['lon']
                    ),
                    'tech_notes': coord.get('notes', '')
                })
                ml_data.append(record)
        else:
            # Se não há coordenadas específicas, usar localização base
            record = base_record.copy()
            record.update({
                'technology_id': f"{plant_id}_base",
                'tech_latitude': base_record['base_latitude'],
                'tech_longitude': base_record['base_longitude'],
                'technology_type': base_record['overall_technology_level'],
                'estimated_area_m2': 0,
                'distance_from_base_m': 0,
                'tech_notes': 'Base location assessment'
            })
            ml_data.append(record)

    return pd.DataFrame(ml_data)

# Carregar dados
df_plantas = load_plant_data()

if df_plantas is not None:
    total_plantas = len(df_plantas)

    # Sidebar - Navegação e Controles
    with st.sidebar:
        st.markdown("### 🎯 NAVEGAÇÃO")

        # Seletor de planta
        current_plant = st.selectbox(
            "Selecionar Planta:",
            range(total_plantas),
            index=st.session_state.plant_index,
            format_func=lambda x: f"{x+1:02d}. {df_plantas.iloc[x]['Municipio']}"
        )
        st.session_state.plant_index = current_plant

        # Navegação rápida
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Anterior", use_container_width=True) and current_plant > 0:
                st.session_state.plant_index = current_plant - 1
                st.rerun()
        with col2:
            if st.button("Próxima ➡️", use_container_width=True) and current_plant < total_plantas - 1:
                st.session_state.plant_index = current_plant + 1
                st.rerun()

        # Progresso
        st.markdown("### 📊 PROGRESSO GERAL")
        assessed_count = len(st.session_state.assessments)
        validated_count = len([a for a in st.session_state.assessments.values()
                             if a.get('validation_status') == 'VALIDATED'])

        progress = assessed_count / total_plantas if total_plantas > 0 else 0
        validation_progress = validated_count / assessed_count if assessed_count > 0 else 0

        st.progress(progress, text=f"Avaliadas: {assessed_count}/{total_plantas} ({progress:.1%})")
        st.progress(validation_progress, text=f"Validadas: {validated_count}/{assessed_count} ({validation_progress:.1%})")

        # Estatísticas compactas
        if assessed_count > 0:
            st.markdown("### 📈 ESTATÍSTICAS")
            tech_levels = [a.get('tech_level', 'UNKNOWN') for a in st.session_state.assessments.values()]

            for level in ['ALTA', 'MEDIA', 'BAIXA', 'SEM_PLANTA']:
                count = tech_levels.count(level)
                if count > 0:
                    st.metric(level.replace('_', ' '), count)

        # Ferramentas de exportação
        st.markdown("### 💾 EXPORTAÇÃO")
        if st.session_state.assessments:
            if st.button("📥 Exportar Dados ML", use_container_width=True):
                ml_df = export_ml_training_data()
                if ml_df is not None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    filename = f'biogas_ml_training_data_{timestamp}.csv'
                    st.download_button(
                        "📊 Baixar CSV para ML",
                        ml_df.to_csv(index=False, encoding='utf-8'),
                        filename,
                        "text/csv",
                        use_container_width=True
                    )

    # Dados da planta atual
    planta = df_plantas.iloc[current_plant]
    plant_id = f"plant_{current_plant:03d}"

    # Layout principal
    col1, col2 = st.columns([2.2, 1.8])

    with col1:
        st.markdown(f"### 📍 Planta {current_plant + 1:02d}/{total_plantas} - {planta['Municipio']}")

        # Informações da planta
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.markdown(f"**📍 Coordenadas Base:** {planta['Latitude']:.6f}, {planta['Longitude']:.6f}")
        with info_col2:
            if 'cana_ha' in planta and pd.notna(planta['cana_ha']):
                st.markdown(f"**🌱 Área de Cana:** {planta['cana_ha']:.0f} ha")

        # Mapa de satélite interativo
        st.markdown("### 🛰️ Análise por Imagem de Satélite")

        existing_coords = st.session_state.technology_coordinates.get(plant_id, [])
        satellite_map = create_assessment_map(
            planta['Latitude'],
            planta['Longitude'],
            planta['Municipio'],
            existing_coords
        )

        map_data = st_folium(
            satellite_map,
            height=550,
            width=None,
            returned_objects=["last_object_clicked", "last_clicked", "all_drawings"]
        )

        # Capturar cliques no mapa para coordenadas de tecnologias
        if map_data['last_object_clicked']:
            clicked_lat = map_data['last_object_clicked']['lat']
            clicked_lon = map_data['last_object_clicked']['lng']

            st.markdown("### 🎯 Coordenada Clicada")
            st.markdown(f"""
            <div class="coord-display">
                <strong>Latitude:</strong> {clicked_lat:.6f}<br>
                <strong>Longitude:</strong> {clicked_lon:.6f}<br>
                <strong>Distância da base:</strong> {calculate_distance(planta['Latitude'], planta['Longitude'], clicked_lat, clicked_lon):.1f}m
            </div>
            """, unsafe_allow_html=True)

            # Interface para adicionar tecnologia
            with st.expander("➕ Adicionar Tecnologia nesta Coordenada"):
                tech_type = st.selectbox(
                    "Tipo de Tecnologia:",
                    ["lagoas", "biotanques", "alta_tech", "outros"],
                    format_func=lambda x: {
                        "lagoas": "🔴 Lagoas/Tanques Grandes",
                        "biotanques": "🟡 Biotanques/Reatores",
                        "alta_tech": "🟢 Alta Tecnologia",
                        "outros": "⚪ Outros"
                    }[x]
                )

                estimated_area = st.number_input("Área Estimada (m²):", min_value=0.0, value=100.0, step=10.0)
                tech_notes = st.text_area("Observações da Tecnologia:", placeholder="Descreva o que observa nesta localização...")

                if st.button("✅ Adicionar Tecnologia"):
                    if plant_id not in st.session_state.technology_coordinates:
                        st.session_state.technology_coordinates[plant_id] = []

                    st.session_state.technology_coordinates[plant_id].append({
                        'lat': clicked_lat,
                        'lon': clicked_lon,
                        'type': tech_type,
                        'area': estimated_area,
                        'notes': tech_notes,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.success("🎯 Tecnologia adicionada com sucesso!")
                    st.rerun()

        # Links diretos
        gmaps_url = f"https://www.google.com/maps/@{planta['Latitude']},{planta['Longitude']},18z"
        earth_url = f"https://earth.google.com/web/@{planta['Latitude']},{planta['Longitude']},0a,300d,35y,0h,0t,0r"

        link_col1, link_col2 = st.columns(2)
        with link_col1:
            st.markdown(f"🔗 [Google Maps]({gmaps_url})")
        with link_col2:
            st.markdown(f"🌍 [Google Earth]({earth_url})")

    with col2:
        st.markdown("### 🔬 AVALIAÇÃO TÉCNICA")

        # Guia de classificação
        with st.expander("📋 Guia de Classificação", expanded=False):
            st.markdown("""
            <div class="tech-indicator tech-pools">
                <strong>🔴 BAIXA TECNOLOGIA:</strong><br>
                • Lagoas de estabilização grandes (&gt;2000m²)<br>
                • Formato irregular, sem cobertura<br>
                • Tratamento anaeróbio simples
            </div>
            <div class="tech-indicator tech-tanks">
                <strong>🟡 MÉDIA TECNOLOGIA:</strong><br>
                • Reatores UASB, CRTs (200-2000m²)<br>
                • Estruturas cilíndricas/retangulares<br>
                • Possível cobertura para biogás
            </div>
            <div class="tech-indicator tech-biogas">
                <strong>🟢 ALTA TECNOLOGIA:</strong><br>
                • Digestores com cúpulas (&lt;200m²)<br>
                • Sistemas integrados de biogás<br>
                • Infraestrutura de purificação
            </div>
            <div class="tech-indicator tech-none">
                <strong>⚠️ SEM PLANTA:</strong><br>
                • Localização sem tecnologias visíveis<br>
                • Apenas coordenada de referência
            </div>
            """, unsafe_allow_html=True)

        # Tecnologias identificadas
        if plant_id in st.session_state.technology_coordinates:
            st.markdown("### 🎯 Tecnologias Mapeadas")
            coords = st.session_state.technology_coordinates[plant_id]

            for i, coord in enumerate(coords):
                with st.expander(f"📍 Tecnologia {i+1} - {coord['type'].replace('_', ' ').title()}"):
                    st.write(f"**Coordenadas:** {coord['lat']:.6f}, {coord['lon']:.6f}")
                    st.write(f"**Área:** {coord['area']:.0f} m²")
                    st.write(f"**Observações:** {coord['notes']}")

                    if st.button(f"🗑️ Remover", key=f"remove_{i}"):
                        st.session_state.technology_coordinates[plant_id].pop(i)
                        st.rerun()

        # Formulário de avaliação
        st.markdown("### 📝 FORMULÁRIO DE AVALIAÇÃO")

        with st.form(f"assessment_form_{plant_id}"):
            # Presença de planta
            has_plant = st.radio(
                "**Existe planta de biogás visível?**",
                [True, False],
                format_func=lambda x: "✅ Sim, há tecnologias visíveis" if x else "❌ Não há planta visível"
            )

            # Nível tecnológico
            if has_plant:
                tech_level = st.radio(
                    "**Nível Tecnológico Predominante:**",
                    ["ALTA", "MEDIA", "BAIXA"],
                    help="Baseado nas tecnologias mapeadas no mapa"
                )
            else:
                tech_level = "SEM_PLANTA"

            # Confiança
            confidence = st.slider(
                "**Confiança na Avaliação (%):**",
                min_value=50,
                max_value=100,
                value=80,
                help="Sua certeza sobre a classificação feita"
            )

            # Observações gerais
            observations = st.text_area(
                "**Observações Gerais:**",
                placeholder="Descreva características gerais da localização, infraestrutura observada, etc.",
                height=100
            )

            # Dados para ML
            ml_notes = st.text_area(
                "**Notas para Treinamento ML:**",
                placeholder="Características específicas que podem ajudar na detecção automática...",
                height=80
            )

            submitted = st.form_submit_button(
                "✅ SALVAR AVALIAÇÃO",
                type="primary",
                use_container_width=True
            )

            if submitted:
                assessment_data = {
                    'plant_index': current_plant,
                    'municipio': planta['Municipio'],
                    'latitude': planta['Latitude'],
                    'longitude': planta['Longitude'],
                    'has_plant': has_plant,
                    'tech_level': tech_level,
                    'confidence': confidence,
                    'observations': observations,
                    'ml_notes': ml_notes,
                    'technology_count': len(st.session_state.technology_coordinates.get(plant_id, [])),
                    'timestamp': datetime.now().isoformat(),
                    'validation_status': 'PENDING',
                    'assessor': 'Prof. Bruna Moraes'
                }

                csv_filename = save_assessment(plant_id, assessment_data)

                # Feedback baseado na confiança e exportação CSV
                if confidence >= 90:
                    st.success(f"🎯 Avaliação salva com alta confiança ({confidence}%)!")
                elif confidence >= 70:
                    st.success(f"✅ Avaliação salva com boa confiança ({confidence}%)!")
                else:
                    st.warning(f"⚠️ Avaliação salva com baixa confiança ({confidence}%). Considere revisar.")

                # Confirmar exportação CSV
                if csv_filename:
                    st.info(f"📊 Dados exportados automaticamente para: {csv_filename}")

                # Auto-avançar
                if current_plant < total_plantas - 1:
                    st.session_state.plant_index = current_plant + 1
                    st.rerun()
                else:
                    st.balloons()
                    st.success("🎉 Todas as plantas foram avaliadas!")

        # Mostrar avaliação atual
        if plant_id in st.session_state.assessments:
            current_assessment = st.session_state.assessments[plant_id]
            status = current_assessment.get('validation_status', 'PENDING')

            st.markdown("### 📋 AVALIAÇÃO ATUAL")
            st.markdown(f"""
            <div class="assessment-card certainty-{'high' if current_assessment['confidence'] >= 80 else 'medium' if current_assessment['confidence'] >= 60 else 'low'}">
                <strong>Status:</strong> {status}<br>
                <strong>Tecnologia:</strong> {current_assessment['tech_level']}<br>
                <strong>Confiança:</strong> {current_assessment['confidence']}%<br>
                <strong>Tecnologias Mapeadas:</strong> {current_assessment.get('technology_count', 0)}
            </div>
            """, unsafe_allow_html=True)

# Seção de validação (para Professor Bruna)
if st.session_state.assessments:
    st.markdown("---")
    st.markdown("## 🔍 PAINEL DE VALIDAÇÃO")

    col1, col2 = st.columns([3, 1])

    with col1:
        pending_assessments = [
            (k, v) for k, v in st.session_state.assessments.items()
            if v.get('validation_status') == 'PENDING'
        ]

        if pending_assessments:
            st.info(f"📋 {len(pending_assessments)} avaliações aguardando validação")

            # Seletor de avaliação para validar
            validation_key = st.selectbox(
                "Selecionar para Validação:",
                [k for k, v in pending_assessments],
                format_func=lambda x: f"{st.session_state.assessments[x]['municipio']} - {st.session_state.assessments[x]['tech_level']}"
            )

            if validation_key:
                assessment = st.session_state.assessments[validation_key]

                st.markdown("### 📊 Dados da Avaliação")
                val_col1, val_col2 = st.columns(2)

                with val_col1:
                    st.write(f"**Município:** {assessment['municipio']}")
                    st.write(f"**Tecnologia:** {assessment['tech_level']}")
                    st.write(f"**Confiança:** {assessment['confidence']}%")

                with val_col2:
                    st.write(f"**Tem Planta:** {'Sim' if assessment.get('has_plant') else 'Não'}")
                    st.write(f"**Tecnologias Mapeadas:** {assessment.get('technology_count', 0)}")
                    st.write(f"**Data:** {assessment['timestamp'][:10]}")

                if assessment.get('observations'):
                    st.write(f"**Observações:** {assessment['observations']}")
        else:
            st.success("✅ Todas as avaliações foram validadas!")

    with col2:
        if pending_assessments and 'validation_key' in locals():
            st.markdown("### ✅ VALIDAÇÃO")

            validation_status = st.selectbox(
                "Status:",
                ["VALIDATED", "NEEDS_REVIEW", "REJECTED"],
                format_func=lambda x: {
                    "VALIDATED": "✅ Validado",
                    "NEEDS_REVIEW": "⚠️ Revisar",
                    "REJECTED": "❌ Rejeitado"
                }[x]
            )

            validation_confidence = st.slider(
                "Confiança da Validação:",
                50, 100, 85
            )

            validation_notes = st.text_area(
                "Notas de Validação:",
                placeholder="Comentários sobre a avaliação...",
                height=100
            )

            if st.button("💾 Salvar Validação", type="primary"):
                st.session_state.assessments[validation_key].update({
                    'validation_status': validation_status,
                    'validation_confidence': validation_confidence,
                    'validation_notes': validation_notes,
                    'validation_date': datetime.now().isoformat(),
                    'validator': 'Prof. Bruna Moraes'
                })

                st.success("✅ Validação salva!")
                st.rerun()

else:
    st.warning("⚠️ Nenhuma avaliação foi realizada ainda.")
    st.info("📋 Use o formulário acima para começar a avaliar as plantas de biogás.")

# Resumo final e estatísticas
if st.session_state.assessments:
    st.markdown("---")
    st.markdown("## 📊 RESUMO ESTATÍSTICO FINAL")

    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

    assessments_list = list(st.session_state.assessments.values())
    tech_levels = [a.get('tech_level', 'UNKNOWN') for a in assessments_list]
    confidences = [a.get('confidence', 0) for a in assessments_list]

    with stats_col1:
        st.metric("🔴 BAIXA", tech_levels.count('BAIXA'))
        st.metric("🟡 MÉDIA", tech_levels.count('MEDIA'))

    with stats_col2:
        st.metric("🟢 ALTA", tech_levels.count('ALTA'))
        st.metric("⚪ SEM PLANTA", tech_levels.count('SEM_PLANTA'))

    with stats_col3:
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        st.metric("📊 Confiança Média", f"{avg_confidence:.1f}%")

        total_coords = sum(len(coords) for coords in st.session_state.technology_coordinates.values())
        st.metric("🎯 Coordenadas Mapeadas", total_coords)

    with stats_col4:
        validated = len([a for a in assessments_list if a.get('validation_status') == 'VALIDATED'])
        st.metric("✅ Validadas", validated)

        completion = len(assessments_list) / total_plantas * 100 if total_plantas > 0 else 0
        st.metric("📈 Progresso", f"{completion:.1f}%")