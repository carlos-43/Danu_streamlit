import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString

#llamada a base de datos completa
df = pd.read_parquet("BaseDeDatosFinal.parquet")

df["orden_compra_timestamp"] = pd.to_datetime(df["orden_compra_timestamp"], errors='coerce')
df["fecha_entrega_al_cliente"] = pd.to_datetime(df["fecha_entrega_al_cliente"], errors='coerce')
df["Mes"] = df["orden_compra_timestamp"].dt.strftime('%B')
df["Año"] = df["orden_compra_timestamp"].dt.year

st.set_page_config(page_title="Dashboard Logístico", layout="wide")
st.title("Operaciones Logísticas - Danu Liverpool")

# Función para calcular calificación de sucursales
def calcular_calificacion_sucursal(df_sucursal):
    """
    Calcula la calificación de una sucursal del 1 al 100 basada en:
    - Porcentaje de % Tardias (peso: 60%)
    - Promedio de días de entrega (peso: 40%)
    """
    # Calcular porcentaje de % Tardias
    total_entregas = len(df_sucursal)
    if total_entregas == 0:
        return 50  # Calificación neutral si no hay datos
    
    entregas_tardias = len(df_sucursal[df_sucursal['estatus_de_entrega'] == 'Tardia'])
    porcentaje_tardias = (entregas_tardias / total_entregas) * 100
    
    # Calcular promedio de días de entrega
    promedio_dias = df_sucursal['tiempo_de_entrega'].mean()
    
    # Normalizar métricas (invertir para que menor sea mejor)
    # Para porcentaje tardías: 0% = 100 puntos, 100% = 0 puntos
    score_tardias = max(0, 100 - porcentaje_tardias)
    
    # Para días de entrega: normalizar usando percentiles del dataset completo
    # Obtener rango global de días de entrega
    dias_min = df['tiempo_de_entrega'].min()
    dias_max = df['tiempo_de_entrega'].max()
    
    # Normalizar días (menos días = mejor score)
    if dias_max > dias_min:
        score_dias = 100 - ((promedio_dias - dias_min) / (dias_max - dias_min)) * 100
    else:
        score_dias = 100
    
    # Combinar scores con pesos
    calificacion_final = (score_tardias * 0.6) + (score_dias * 0.4)
    
    # Asegurar que esté entre 1 y 100
    return max(1, min(100, round(calificacion_final)))


# hide_streamlit_style = """
#     <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
#     </style>
# """

# st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# Opción 1: Función para generar CSS dinámico
def aplicar_css_global():
    # Determinar el estado del overflow basado en tabla_activa
    overflow_y = "hidden" if st.session_state.get('tabla_activa') == 'sucursales' else "auto"
    
    st.markdown(f"""
        <style>
            .back-button-right {{
                display: flex !important;
                justify-content: flex-end !important;
                align-items: center !important;
                padding-right: 0px !important;
            }}
            /* Layout principal - altura fija para la página */
            .main .block-container {{
                height: 100vh !important;
                max-height: 100vh !important;
                overflow: hidden !important;
                padding-top: 0px !important;
                padding-left: 35px !important;
                padding-right: 35px !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            
            /* Hacer que el título sea más compacto */
            h1 {{
                margin-bottom: -40px !important;
                flex-shrink: 0 !important;
                padding: 25px 0 0 0;
            }}
            
            /* KPIs fijos en la parte superior */
            .kpi-container {{
                flex-shrink: 0 !important;
                margin-bottom: 0px !important;
                margin-top: 0px !important;
            }}
            
            /* Contenedor de tabs fijo */
            .stTabs {{
                display: flex !important;
                flex-direction: column !important;
                flex: 1 !important;
                min-height: 0 !important;
            }}
            
            /* Tab list fijo */
            div[data-baseweb="tab-list"] {{
                padding-top: 0 !important;
                flex-shrink: 0 !important;
            }}
            
            /* Panel de contenido con scroll dinámico */
            .stTabs [data-baseweb="tab-panel"] {{
                background-color: white !important;
                border-radius: 16px !important;
                padding: 25px !important;
                padding-bottom: 120px !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
                margin: 15px 0 !important;
                flex: 1 !important;
                overflow-y: {overflow_y} !important;
                overflow-x: hidden !important;
                min-height: 0 !important;
                max-height: calc(100vh - 290px) !important;
            }}
            
            /* Sidebar styles */
            [data-testid="stSidebarHeader"] {{
                display: none;
            }}
            [data-testid="stSidebar"] {{
                background-color: #07084D !important;
                width: 240px !important;
                min-width: 240px !important;
                max-width: 240px !important;
            }}
            [data-testid="stSidebar"] * {{
                color: white !important;
            }}
            [data-testid="stSidebar"] label {{
                color: white !important;
            }}
                
            .stSlider .css-1o1z36u {{
                color: white !important;
            }}

            .stMultiSelect span {{
                color: white !important;
            }}
            [data-testid="stSidebar"] .st-bm {{
                color: black !important;
            }}
            .st-cl svg {{
                color: black !important;
                fill: black !important;
            }}
            h3 {{
                padding-bottom: 0px !important;
                margin-bottom: 0.5rem !important;
            }}
            .main {{
                background-color: #F5F5F5;
            }}

            /* Tarjetas para KPIs */
            .kpi-card {{
                background-color: white;
                border: .5px solid rgb(7, 8, 77); 
                border-radius: 16px;
                padding: 10px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
                text-align: center;
            }}

            .kpi-title {{
                font-size: 15px;
                color: #07084D90;
                font-weight: Medium;
            }}

            .kpi-value {{
                font-size: 33px;
                font-weight: Bold;
                color: #07084D;
            }}

            .main-section-card {{
                background-color: white;
                border-radius: 16px;
                padding: 0px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
                margin: 20px 0;
                overflow-y: auto;
                overflow-x: hidden;
            }}

            .section-title {{
                font-size: 24px;
                font-weight: bold;
                color: #07084D;
                margin-bottom: 20px;
                text-align: left;
            }}

            .top-estados-container {{
                display: flex;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 15px;
                width: 100%;
            }}

            .stDataFrame tbody tr td:last-child {{
                font-weight: bold !important;
            }}

            .section-separator {{
                border-top: 2px solid #E5E7EB;
                margin: 30px 0 50px 0;
            }}

            .criticidad-card {{
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 25px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }}

            .criticidad-critica {{
                background-color: #FEE2E2;
                border-left: 6px solid #DC2626;
            }}

            .criticidad-media {{
                background-color: #FEF3C7;
                border-left: 6px solid #F59E0B;
            }}

            .criticidad-baja {{
                background-color: #D1FAE5;
                border-left: 6px solid #10B981;
            }}

            .criticidad-titulo {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }}

            .criticidad-texto {{
                font-size: 16px;
                margin-bottom: 5px;
            }}

            .criticidad-porcentaje {{
                font-size: 28px;
                font-weight: bold;
            }}
            
            [data-baseweb="tab"] p {{
                font-size: 16px !important;
                font-weight: normal !important;  
                margin: 10px !important;
            }}
            
            [data-baseweb="tab"][aria-selected="true"] p {{
                font-size: 18px !important;
                font-weight: bold !important;
            }}
            /* Hacer más grandes los headers de las tablas de datos */
            .stDataFrame thead th {{
                font-size: 18px !important;
                font-weight: bold !important;
                padding: 12px 8px !important;
            }}
            
            /* Hacer más grandes los datos de las tablas */
            .stDataFrame tbody td {{
                font-size: 163px !important;
                padding: 10px 8px !important;
            }}
            
            /* Hacer más grandes los valores numéricos en negrita */
            .stDataFrame tbody tr td:last-child {{
                font-weight: bold !important;
                font-size: 17px !important;
            }}
            
            /* Hacer más grandes los títulos de los gráficos */
            .js-plotly-plot .plotly .gtitle {{
                font-size: 20px !important;
                font-weight: bold !important;
            }}
            
            /* Hacer más grandes las leyendas de los gráficos */
            .js-plotly-plot .plotly .legend text {{
                font-size: 13.5px !important;
            }}
            
            /* Hacer más grandes las etiquetas de los ejes */
            .js-plotly-plot .plotly .xtick text {{
                font-size: 15px !important;
            }}
            
            /* Hacer más grandes los valores en las barras y sectores del pie */
            .js-plotly-plot .plotly .bar text,
            .js-plotly-plot .plotly .pie text {{
                font-size: 18px !important;
                font-weight: bold !important;
            }}
            
            /* Hacer más grandes los subtítulos tipo h2 del tab */
            .stTabs [data-baseweb="tab-panel"] h2 {{
                font-size: 32px !important;
                font-weight: bold !important;
            }}
            
            /* Hacer más grandes los textos generales dentro del tab */
            .stTabs [data-baseweb="tab-panel"] p {{
                font-size: 16px !important;
            }}
            
            /* Hacer más grandes los textos de elementos específicos */
            .stTabs [data-baseweb="tab-panel"] div[data-testid="column"] {{
                font-size: 16px !important;
            }}
            
            /* Hacer más grandes los números de las métricas en dataframes */
            .stDataFrame tbody td[data-testid="cell"] {{
                font-size: 16px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

# Uso de la función
aplicar_css_global()

# Opción 2: CSS con clases condicionales
def aplicar_css_con_clases():
    st.markdown("""
        <style>
            /* ... todo tu CSS existente ... */
            
            /* Panel de contenido - estado por defecto */
            .stTabs [data-baseweb="tab-panel"] {
                background-color: white !important;
                border-radius: 16px !important;
                padding: 25px !important;
                padding-bottom: 120px !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
                margin: 15px 0 !important;
                flex: 1 !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
                min-height: 0 !important;
                max-height: calc(100vh - 295px) !important;
            }
            
            /* Panel cuando tabla sucursales está activa */
            .tabla-sucursales-activa .stTabs [data-baseweb="tab-panel"] {
                overflow-y: hidden !important;
            }
            
            /* Panel cuando tabla estados está activa */
            .tabla-estados-activa .stTabs [data-baseweb="tab-panel"] {
                overflow-y: auto !important;
            }
        </style>
    """, unsafe_allow_html=True)

# Opción 3: Usando session_state directamente en el CSS
def aplicar_css_session_state():
    # Obtener el estado actual
    tabla_activa = st.session_state.get('tabla_activa', 'estados')
    
    # CSS base
    css_base = """
        <style>
            /* Todo tu CSS existente aquí */
            .back-button-right {
                display: flex !important;
                justify-content: flex-end !important;
                align-items: center !important;
                padding-right: 0px !important;
            }
            /* ... resto de estilos ... */
    """
    
    # CSS dinámico para el panel
    if tabla_activa == 'sucursales':
        css_panel = """
            .stTabs [data-baseweb="tab-panel"] {
              
                overflow-y: hidden !important;
                overflow-x: hidden !important;
                
            }
        """
    else:
        css_panel = """
            .stTabs [data-baseweb="tab-panel"] {
                background-color: white !important;
                border-radius: 16px !important;
                padding: 25px !important;
                padding-bottom: 120px !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
                margin: 15px 0 !important;
                flex: 1 !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
                min-height: 0 !important;
                max-height: calc(100vh - 295px) !important;
            }
        """
    
    # Cerrar el bloque CSS
    css_close = """
        </style>
    """
    
    # Aplicar CSS completo
    st.markdown(css_base + css_panel + css_close, unsafe_allow_html=True)


# Inicializar estados de sesión
if 'selected_estado' not in st.session_state:
    st.session_state.selected_estado = None
if 'selected_sucursal' not in st.session_state:
    st.session_state.selected_sucursal = None
if 'tabla_activa' not in st.session_state:
    st.session_state.tabla_activa = 'estados'  # 'estados' o 'sucursales'

#filter side menu
st.sidebar.image("logo1.png", use_column_width=True)
st.sidebar.header("Filtros")

# CAMBIO 1: Agregar filtro de año
años_disponibles = sorted(df['Año'].dropna().unique())
año_seleccionado = st.sidebar.selectbox("Año", ['Todos'] + [str(año) for año in años_disponibles])

estados_cliente = sorted(df['estado_cliente'].dropna().unique())

# Filtro de estado en sidebar (solo afecta KPIs y gráficas, no las tablas)
estado_cliente = st.sidebar.selectbox(
    "Estado del Cliente", 
    ['Todos'] + estados_cliente
)

# Filtros del sidebar (aplicados a KPIs y gráficas)
df_sidebar_filtered = df.copy()

# Aplicar filtro de año
if año_seleccionado != "Todos":
    df_sidebar_filtered = df_sidebar_filtered[df_sidebar_filtered["Año"] == int(año_seleccionado)]

if estado_cliente != "Todos":
    df_sidebar_filtered = df_sidebar_filtered[df_sidebar_filtered["estado_cliente"] == estado_cliente]

estatus = st.sidebar.selectbox("Estatus de Entrega", ['Todos'] + sorted(df['estatus_de_entrega'].dropna().unique()))

tiempo_min, tiempo_max = int(df["tiempo_de_entrega"].min()), int(df["tiempo_de_entrega"].max())
rango_tiempo = st.sidebar.slider("Rango de Entrega (días)", tiempo_min, tiempo_max, (tiempo_min, tiempo_max))

with st.sidebar.expander("Filtros Temporales", expanded=False):
    meses = st.multiselect("Mes de Compra", df['Mes'].dropna().unique(), default=df['Mes'].dropna().unique())
    dias_semana = st.multiselect("Día de Entrega", df['dia_de_la_semana_entrega'].dropna().unique(), default=df['dia_de_la_semana_entrega'].dropna().unique())
    tipos_dia = st.multiselect("Tipo de Día", df['tipo_dia_transportista'].dropna().unique(), default=df['tipo_dia_transportista'].dropna().unique())

# Aplicar filtros del sidebar (para KPIs y gráficas)
if estatus != 'Todos':
    df_sidebar_filtered = df_sidebar_filtered[df_sidebar_filtered["estatus_de_entrega"] == estatus]

filtros_tiempo = (
    df_sidebar_filtered["tiempo_de_entrega"].between(rango_tiempo[0], rango_tiempo[1]) &
    df_sidebar_filtered["Mes"].isin(meses) &
    df_sidebar_filtered["dia_de_la_semana_entrega"].isin(dias_semana) &
    df_sidebar_filtered["tipo_dia_transportista"].isin(tipos_dia)
)
df_sidebar_filtered = df_sidebar_filtered[filtros_tiempo]

# Para los KPIs y gráficas, usar df_sidebar_filtered
df_filtered = df_sidebar_filtered.copy()
df_filtered['estatus_de_entrega'] = pd.Categorical(
    df_filtered['estatus_de_entrega'],
    categories=['Tardia','A tiempo', 'Temprana'],
    ordered=True
)

# Para las tablas, usar filtros independientes (sin filtro de estado del sidebar)
df_table_filtered = df.copy()

# Aplicar solo filtros que no sean el estado del cliente
if año_seleccionado != "Todos":
    df_table_filtered = df_table_filtered[df_table_filtered["Año"] == int(año_seleccionado)]

if estatus != 'Todos':
    df_table_filtered = df_table_filtered[df_table_filtered["estatus_de_entrega"] == estatus]

filtros_tiempo_table = (
    df_table_filtered["tiempo_de_entrega"].between(rango_tiempo[0], rango_tiempo[1]) &
    df_table_filtered["Mes"].isin(meses) &
    df_table_filtered["dia_de_la_semana_entrega"].isin(dias_semana) &
    df_table_filtered["tipo_dia_transportista"].isin(tipos_dia)
)
df_table_filtered = df_table_filtered[filtros_tiempo_table]

# Contenedor para KPIs - AHORA CON CLASE ESPECÍFICA
st.markdown('<div class="kpi-container">', unsafe_allow_html=True)

#kpi section (4) - MODIFICADO: Cambiar Órdenes Totales por Valor Total
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Calcular valor total (costo_de_flete + precio)
    valor_total = (df_filtered['costo_de_flete'] + df_filtered['precio']).sum()

    if valor_total >= 1_000_000:
        valor_total_formatted = f"${valor_total / 1_000_000:.1f}M"
    elif valor_total >= 1_000:
        valor_total_formatted = f"${valor_total / 1_000:.1f}K"
    else:
        valor_total_formatted = f"${valor_total:,.0f}"

    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Valor Total Órdenes</div>
            <div class="kpi-value">{valor_total_formatted}</div>
        </div>
    """, unsafe_allow_html=True)


with col2:
    # Calcular número de clientes únicos
    num_clientes = df_filtered['id_cliente'].nunique()
    
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Número de Clientes</div>
            <div class="kpi-value">{num_clientes:,}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Sucursales</div>
            <div class="kpi-value">{df_filtered['sucursal_asignada'].nunique()}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Días Prom. Entrega</div>
            <div class="kpi-value">{df_filtered['tiempo_de_entrega'].mean():.2f}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

#menu de los 3 tableros/tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Forecast", "Calculadora", "Rutas Reales"])


######
#TAB1 
#####
with tab1:
# Header row con botón de regreso alineado a la derecha
    if st.session_state.tabla_activa == 'sucursales' and st.session_state.selected_estado:
        col_title, col_button = st.columns([4, 1], gap="small")
        
        with col_title:
            st.markdown(f"""
                <h2 style="margin: 0; padding: 0; color: #07084D; font-size: 28px; font-weight: bold;">
                    Detalle de Sucursales {st.session_state.selected_estado}
                </h2>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
            <h2 style="margin: 0; padding: 0; color: #07084D; font-size: 28px; font-weight: bold;">
                Operation Insights
            </h2>
        """, unsafe_allow_html=True)
    
    # Separador reducido
    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
    # Layout condicional según el tipo de tabla activa
    if st.session_state.tabla_activa == 'estados':
        # VISTA DE ESTADOS: Tabla + Pie Chart (layout 50/50)
        col1, col2 = st.columns(2, gap="medium")
        
        # TABLA DE ESTADOS
        with col1:
            estados_summary = df_table_filtered.groupby(['estado_cliente', 'estatus_de_entrega']).size().unstack(fill_value=0).reset_index()
            
            # Asegurar que todas las columnas de estatus existan
            for estatus in ['Tardia', 'A tiempo', 'Temprana']:
                if estatus not in estados_summary.columns:
                    estados_summary[estatus] = 0
            
            # Reordenar columnas y renombrar
            estados_summary = estados_summary[['estado_cliente', 'Tardia', 'A tiempo', 'Temprana']]
            estados_summary.columns = ['Estado', 'Tardia', 'A tiempo', 'Temprana']
            
            # Agregar columna de Total de Órdenes
            estados_summary['Total Órdenes'] = estados_summary['Tardia'] + estados_summary['A tiempo'] + estados_summary['Temprana']
            
            # Calcular % T. Local (porcentaje de tardías respecto al total de órdenes por estado)
            estados_summary['% T. Local'] = (estados_summary['Tardia'] / estados_summary['Total Órdenes'] * 100).round(1)
            
            # Calcular % T. Global (porcentaje de tardías de cada estado respecto al total global de órdenes)
            total_global_ordenes = estados_summary['Total Órdenes'].sum()
            estados_summary['% T. Global'] = (estados_summary['Tardia'] / total_global_ordenes * 100).round(1)
            
            # Seleccionar solo las columnas que queremos mostrar (reordenadas)
            estados_summary_final = estados_summary[['Estado', '% T. Global', '% T. Local', 'Total Órdenes']].copy()
            
            # Ordenar por % T. Global (descendente)
            estados_summary_final = estados_summary_final.sort_values('% T. Global', ascending=False)
            
            # Tabla interactiva con evento de selección para ir a sucursales
            event = st.dataframe(
                estados_summary_final,
                height=400,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Estado": st.column_config.TextColumn("Estado", width=120),
                    "% T. Global": st.column_config.NumberColumn("% T. Global", width="small", format="%.1f%%"),
                    "% T. Local": st.column_config.NumberColumn("% T. Local", width="small", format="%.1f%%"),
                    "Total Órdenes": st.column_config.NumberColumn("Total Órdenes", width="small")
                }
            )
            
            # Manejar el evento de selección para cambiar a vista de sucursales
            if len(event.selection.rows) > 0:
                selected_row = event.selection.rows[0]
                selected_estado = estados_summary_final.iloc[selected_row]['Estado']
                
                # Cambiar a vista de sucursales del estado seleccionado
                st.session_state.selected_estado = selected_estado
                st.session_state.tabla_activa = 'sucursales'
                st.session_state.selected_sucursal = None  # Reset sucursal selection
                st.rerun()

        # PIE CHART para vista de estados
        with col2:
            orden_labels = ["Tardia", "Temprana", "A tiempo"]
            colores = ["#07084D", "#C5CAF9", "#596FC9"]

            # Determinar qué datos usar para las gráficas
            if st.session_state.selected_sucursal:
                # Filtrar por sucursal específica seleccionada
                df_charts = df_filtered[df_filtered['sucursal_asignada'] == st.session_state.selected_sucursal]
            else:
                # Usar todos los datos filtrados
                df_charts = df_filtered

            df_pie = df_charts[df_charts["estatus_de_entrega"].isin(orden_labels)]
            df_pie["estatus_de_entrega"] = pd.Categorical(df_pie["estatus_de_entrega"], categories=orden_labels, ordered=True)

            # Calcular tanto cantidad como valor monetario por estatus
            df_pie_grouped = df_pie.groupby("estatus_de_entrega").agg({
                'orden_compra_timestamp': 'count',  # Cantidad de órdenes
                'costo_de_flete': 'sum',
                'precio': 'sum'
            }).reset_index()
            
            # Calcular valor total por estatus
            df_pie_grouped['valor_total'] = df_pie_grouped['costo_de_flete'] + df_pie_grouped['precio']
            df_pie_grouped.columns = ["Estatus", "Cantidad", "Costo_Flete", "Precio", "Valor_Total"]
            
            # Reindexar para asegurar el orden correcto
            df_pie_grouped = df_pie_grouped.set_index('Estatus').reindex(orden_labels).reset_index()
            df_pie_grouped = df_pie_grouped.fillna(0)

            # Función para formatear valores monetarios
            def format_currency(value):
                if value >= 1_000_000:
                    return f"${value / 1_000_000:.1f}M"
                elif value >= 1_000:
                    return f"${value / 1_000:.1f}K"
                else:
                    return f"${value:,.0f}"

            # Crear el pie chart usando la cantidad para el tamaño de los sectores
            pie_chart = px.pie(
                df_pie_grouped,
                names="Estatus",
                values="Cantidad",
                color="Estatus",
                color_discrete_map=dict(zip(orden_labels, colores))
            )

            # Crear texto personalizado que incluya porcentaje y valor monetario
            def create_custom_text(df):
                total_cantidad = df['Cantidad'].sum()
                custom_text = []
                
                for idx, row in df.iterrows():
                    porcentaje = (row['Cantidad'] / total_cantidad) * 100 if total_cantidad > 0 else 0
                    valor_formateado = format_currency(row['Valor_Total'])
                    custom_text.append(f"<b>{porcentaje:.1f}%</b><br>({valor_formateado})")
                
                return custom_text

            # Aplicar el texto personalizado
            custom_text = create_custom_text(df_pie_grouped)
            
            pie_chart.update_traces(
                textinfo='text',
                text=custom_text,
                textfont=dict(size=16, family='Arial', color='white')
            )

            # Altura fija del gráfico (maximizada)
            pie_chart.update_layout(
                height=440,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12)
                ),
                margin=dict(t=20, b=60, l=20, r=20),
                showlegend=True
            )

            st.plotly_chart(pie_chart, use_container_width=True)
    
    else:  # tabla_activa == 'sucursales'
        # VISTA DE SUCURSALES: Solo tabla + gráfica de entregas por día
        col1, col2 = st.columns(2, gap="medium")
        
        # TABLA DE SUCURSALES DEL ESTADO SELECCIONADO
        with col1:
            df_estado_selected = df_table_filtered[df_table_filtered['estado_cliente'] == st.session_state.selected_estado]
            
            # Crear tabla de resumen por sucursales
            sucursales_summary = df_estado_selected.groupby(['sucursal_asignada', 'estatus_de_entrega']).size().unstack(fill_value=0).reset_index()
            
            # Asegurar que todas las columnas de estatus existan
            for estatus in ['Tardia', 'A tiempo', 'Temprana']:
                if estatus not in sucursales_summary.columns:
                    sucursales_summary[estatus] = 0
            
            # Reordenar columnas y renombrar
            sucursales_summary = sucursales_summary[['sucursal_asignada', 'Tardia', 'A tiempo', 'Temprana']]
            sucursales_summary.columns = ['Sucursal', 'Tardia', 'A tiempo', 'Temprana']
            
            # Agregar columna de Total de Pedidos (nombre diferente para distinguir de estados)
            sucursales_summary['Órdenes'] = sucursales_summary['Tardia'] + sucursales_summary['A tiempo'] + sucursales_summary['Temprana']
            
            # Calcular % Tardias (nombre diferente para distinguir de estados)
            sucursales_summary['% Tardias'] = (sucursales_summary['Tardia'] / sucursales_summary['Órdenes'] * 100).round(1)
            
            # Calcular calificación para cada sucursal
            calificaciones = []
            for sucursal in sucursales_summary['Sucursal']:
                df_sucursal = df_estado_selected[df_estado_selected['sucursal_asignada'] == sucursal]
                calificacion = calcular_calificacion_sucursal(df_sucursal)
                calificaciones.append(calificacion)
            
            sucursales_summary['Puntuación'] = calificaciones
            
            # Seleccionar las columnas finales con nombres personalizados
            sucursales_summary_final = sucursales_summary[['Sucursal', 'Puntuación', '% Tardias', 'Órdenes']].copy()
            
            # Ordenar por Órdenes en orden descendente
            sucursales_summary_final = sucursales_summary_final.sort_values('Órdenes', ascending=False)
            
            # Reemplazar valores None/NaN con cadenas vacías
            sucursales_summary_final = sucursales_summary_final.fillna('')
            
            # AGREGAR FILA DE REGRESO AL INICIO
            regreso_row = pd.DataFrame({
                'Sucursal': ['← Regresar a tabla de estados'],
                'Puntuación': [''],
                '% Tardias': [''],
                'Órdenes': ['']
            })
            
            # Concatenar la fila de regreso al inicio de la tabla
            sucursales_summary_final = pd.concat([regreso_row, sucursales_summary_final], ignore_index=True)
            
            # Envolver la tabla con la clase CSS específica para desactivar scroll
            st.markdown('<div class="sucursales-table">', unsafe_allow_html=True)
            
            # Tabla interactiva con evento de selección para filtrar gráficas
            event = st.dataframe(
                sucursales_summary_final,
                height=400,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Sucursal": st.column_config.TextColumn("Sucursal", width=180),
                    "Puntuación": st.column_config.NumberColumn("Puntuación", width="small", format="%s"),
                    "% Tardias": st.column_config.NumberColumn("% Tardias", width="small", format="%s"),
                    "Órdenes": st.column_config.NumberColumn("Órdenes", width="small", format="%s")
                }
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Manejar selección de sucursal para filtrar gráficas
            if len(event.selection.rows) > 0:
                selected_row = event.selection.rows[0]
                selected_sucursal = sucursales_summary_final.iloc[selected_row]['Sucursal']
                
                # Si se selecciona la fila de regreso
                if selected_sucursal == '← Regresar a tabla de estados':
                    st.session_state.tabla_activa = 'estados'
                    st.session_state.selected_estado = None
                    st.session_state.selected_sucursal = None
                    st.rerun()
                else:
                    # Selección normal de sucursal
                    if st.session_state.selected_sucursal != selected_sucursal:
                        st.session_state.selected_sucursal = selected_sucursal
                        st.rerun()

        # GRÁFICA DE ENTREGAS POR DÍA para vista de sucursales (SIN TÍTULO)
        with col2:
            # Determinar qué datos usar para la gráfica
            if st.session_state.selected_sucursal:
                # Filtrar por sucursal específica seleccionada
                df_charts = df_filtered[df_filtered['sucursal_asignada'] == st.session_state.selected_sucursal]
            else:
                # Usar todos los datos filtrados del estado seleccionado
                df_charts = df_filtered[df_filtered['estado_cliente'] == st.session_state.selected_estado]

            # Configuración de la gráfica
            chart_height = 440  # Misma altura que el pie chart
            color_discrete_map = {
                'Tardia': '#07084D',
                'Temprana': '#596FC9',
                'A tiempo': '#50C878',
            }
            estatus_orden = ['Tardia', 'Temprana', 'A tiempo']
            
            # Definir mapeo de días de inglés a español
            dias_mapping = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes', 
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }

            # Crear una copia del dataframe filtrado para modificar
            df_grafica = df_charts.copy()

            # Convertir los días de inglés a español
            df_grafica['dia_de_la_semana_entrega_es'] = df_grafica['dia_de_la_semana_entrega'].map(dias_mapping)

            # Definir el orden correcto de los días de la semana en español
            dias_semana_orden_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            fig_day = px.histogram(
                df_grafica,
                x="dia_de_la_semana_entrega_es",
                color="estatus_de_entrega",
                barmode="group",
                color_discrete_map=color_discrete_map,
                category_orders={
                    'estatus_de_entrega': estatus_orden,
                    'dia_de_la_semana_entrega_es': dias_semana_orden_es
                },
                height=chart_height
            )

            fig_day.update_layout(
                xaxis_title=None,
                yaxis_title=None,
                height=chart_height,
                margin=dict(t=0, b=0, l=0, r=0),
                showlegend=False
            )

            st.plotly_chart(fig_day, use_container_width=True)
    
    # Separador solo para vista de estados (donde se muestran las gráficas adicionales)
    if st.session_state.tabla_activa == 'estados':
        st.markdown("<div style='margin: 0px 0;'></div>", unsafe_allow_html=True)
        
        # Configuración de gráficas adicionales (solo para vista de estados)
        chart_height = 350  
        color_discrete_map = {
            'Tardia': '#07084D',
            'Temprana': '#596FC9',
            'A tiempo': '#50C878',
        }
        estatus_orden = ['Tardia', 'Temprana', 'A tiempo']
        
        # Definir mapeo de días de inglés a español
        dias_mapping = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes', 
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }

        # Crear una copia del dataframe filtrado para modificar
        df_grafica = df_filtered.copy()

        # Convertir los días de inglés a español
        df_grafica['dia_de_la_semana_entrega_es'] = df_grafica['dia_de_la_semana_entrega'].map(dias_mapping)

        # Definir el orden correcto de los días de la semana en español
        dias_semana_orden_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        fig_day = px.histogram(
            df_grafica,
            x="dia_de_la_semana_entrega_es",
            color="estatus_de_entrega",
            barmode="group",
            title="Entregas por Día",
            color_discrete_map=color_discrete_map,
            category_orders={
                'estatus_de_entrega': estatus_orden,
                'dia_de_la_semana_entrega_es': dias_semana_orden_es
            },
            height=chart_height
        )

        fig_day.update_layout(
            title=dict(
                text="Entregas por Día",
                y=1.00,
                x=0.05,
                xanchor='left',
                yanchor='top',
                font=dict(size=16)
            ),
            xaxis_title=None,
            yaxis_title=None,
            height=chart_height,
            margin=dict(t=60, b=0, l=0, r=0),
            legend=dict(
                title_text="",      
                orientation="h",    
                yanchor="bottom",
                y=1.02,             
                xanchor="left",     
                x=-0.1                  
            )
        )

        
        # Gráfica de categorías
        top_categorias = df_filtered['categoria_nombre_producto'].value_counts().reset_index()
        top_categorias.columns = ['Categoría', 'Cantidad']
        top_categorias = top_categorias.head(10)
        colores_personalizados = ['#596FC9' if i < 3 else '#C5CAF9' for i in range(len(top_categorias))]

        def get_text_values(data):
            return [f'{val/1000:.0f}K' if val >= 1000 else str(val) for val in data['Cantidad']]
        
        fig_bar = px.bar(
            top_categorias, 
            x='Cantidad', 
            y='Categoría',
            orientation='h',
            color=top_categorias['Categoría'],
            color_discrete_sequence=colores_personalizados,
            height=chart_height,
            text=get_text_values(top_categorias) 
        )

        fig_bar.update_traces(
            textposition='inside',
            textfont=dict(color='white', size=11, family='Arial Black'),
            marker=dict(cornerradius=4),
            width=0.9
        )
        fig_bar.update_layout(
            title=dict(
                text="Top Categorías",
                y=1.00,
                x=0.05,
                xanchor='left',
                yanchor='top',
                font=dict(size=15)
            ),
            yaxis=dict(categoryorder='total ascending'),
            xaxis_title=None,
            yaxis_title=None,
            bargap=0.9,
            showlegend=False,
            height=chart_height,
            margin=dict(t=60, b=0, l=0, r=0),
        )

        # Layout 50/50 para las gráficas de análisis (solo en vista de estados)
        col1, col2 = st.columns([1, 1], gap="medium")  
        
        with col1:
            st.plotly_chart(fig_day, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_bar, use_container_width=True)

# # #checkpoint tab1#



##################################################################################################################################
##################################################################################################################################
####################################################MODELO DE MACHINE LEARNING####################################################
# ──────────── IMPORTS NECESARIOS ────────────
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import xgboost as xgb

@st.cache_data
def entrenar_modelo_ml():
    """
    Función para entrenar el modelo ML una sola vez y guardarlo
    """
    # Cargar datos de entrenamiento
    file_path = "BaseDeDatosFinal_ajustado2.parquet"
    df = pd.read_parquet(file_path)
    
    # Preparación de datos
    df['estatus_binario'] = df['estatus_de_entrega'].map({'Tardia': 1, 'Temprana': 0, 'A tiempo': 0})
    df = df.drop_duplicates(subset='order_id')
    
    features = [
        'distancia_categoria', 
        'categoria_nombre_producto', 
        'peso_producto_g', 
        'volume_cm3', 
        'distancia_sucursal_cd_km', 
        'centro_distribucion',
        'sucursal_asignada',
        'precio',
        'costo_de_flete',
        'region'
    ]
    
    target = 'estatus_binario'
    df_model = df[features + [target]].dropna()
    
    X = df_model[features]
    y = df_model[target].astype(int)
    
    # Identificar tipos de variables
    cat_features = X.select_dtypes(include='object').columns.tolist()
    num_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Preprocesamiento
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
    ])
    
    X_preprocessed = preprocessor.fit_transform(X)
    if hasattr(X_preprocessed, 'toarray'):
        X_preprocessed = X_preprocessed.toarray()
    
    # SMOTE y división
    smote_global = SMOTE(sampling_strategy=1.0, random_state=42)
    X_res, y_res = smote_global.fit_resample(X_preprocessed, y)
    
    X_train_g, X_test_g, y_train_g, y_test_g = train_test_split(
        X_res, y_res, test_size=0.30, random_state=42, stratify=y_res
    )
    
    # Entrenar modelo
    model = xgb.XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=7,
        random_state=42,
        eval_metric="logloss"
    )
    
    model.fit(X_train_g, y_train_g)
    
    return model, preprocessor, features

@st.cache_data
def aplicar_modelo_ml(df_input, _model, _preprocessor, features):
    """
    Aplica el modelo entrenado a nuevos datos
    """
    try:
        # Verificar que el DataFrame tenga las columnas necesarias
        df_trabajo = df_input.copy()
        
        # Verificar columnas requeridas
        columnas_faltantes = set(features) - set(df_trabajo.columns)
        if columnas_faltantes:
            st.warning(f"Columnas faltantes para el modelo: {columnas_faltantes}")
            # Usar solo las columnas disponibles o crear valores por defecto
            for col in columnas_faltantes:
                df_trabajo[col] = 0  # O algún valor por defecto apropiado
        
        # Seleccionar solo las features del modelo
        X_new = df_trabajo[features]
        
        # Aplicar preprocesamiento
        X_new_preprocessed = _preprocessor.transform(X_new)
        if hasattr(X_new_preprocessed, 'toarray'):
            X_new_preprocessed = X_new_preprocessed.toarray()
        
        # Hacer predicciones
        probabilidades = _model.predict_proba(X_new_preprocessed)[:, 1]
        predicciones = _model.predict(X_new_preprocessed)
        
        # Mapear predicciones binarias a estatus
        estatus_predicho = ['En Riesgo' if pred == 1 else 'A Tiempo' for pred in predicciones]
        
        # Agregar probabilidades y estatus al DataFrame original
        df_resultado = df_input.copy()
        df_resultado['probabilidad_tardia'] = probabilidades
        df_resultado['estatus_predicho'] = estatus_predicho
        
        return df_resultado
        
    except Exception as e:
        st.error(f"Error al aplicar el modelo: {str(e)}")
        # Fallback: retornar df original con probabilidades aleatorias
        df_fallback = df_input.copy()
        df_fallback['probabilidad_tardia'] = np.random.random(len(df_input)) * 0.5
        df_fallback['estatus_predicho'] = ['A Tiempo'] * len(df_input)
        return df_fallback

# ====== IMPLEMENTACIÓN PRINCIPAL ======

# Entrenar modelo (se ejecuta una sola vez gracias al cache)
try:
    model, preprocessor, features = entrenar_modelo_ml()
except Exception as e:
    st.error(f"Error al entrenar el modelo: {str(e)}")
    model, preprocessor, features = None, None, None

####################################################
# TAB 2 - PREDICCIONES CON DATOS DEL USUARIO
####################################################
with tab2:

    st.markdown("<h3 style='font-size: 22px;'>Ingresa tu base de datos</h4>", unsafe_allow_html=True)

    # HTML para ocultar el espacio del label del file_uploader
    hide_label_css = """
        <style>
        div[data-testid="stFileUploader"] > label {
            display: none;
        }
        </style>
    """
    st.markdown(hide_label_css, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "",  
        type=['csv', 'xlsx', 'parquet'],
    )
    
    df_usuario = None
    
    if uploaded_file is not None:
        try:
            # Leer el archivo según su extensión
            if uploaded_file.name.endswith('.csv'):
                df_usuario = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df_usuario = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.parquet'):
                df_usuario = pd.read_parquet(uploaded_file)
            
            st.success(f"Archivo cargado exitosamente: {len(df_usuario)} registros")
            
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")
    
    # ====== APLICAR MODELO A LOS DATOS DEL USUARIO ======
    st.markdown("---")
    
    # Verificar si tenemos datos del usuario y el modelo está disponible
    if df_usuario is not None and model is not None:
        # Aplicar filtro de estado si está seleccionado
        df_para_prediccion = df_usuario.copy()
        if estado_cliente != "Todos" and 'estado_cliente' in df_para_prediccion.columns:
            df_para_prediccion = df_para_prediccion[df_para_prediccion['estado_cliente'] == estado_cliente]
        
        with st.spinner("Aplicando modelo de Machine Learning..."):
            df_prediccion_usuario = aplicar_modelo_ml(df_para_prediccion, model, preprocessor, features)
        
        import plotly.graph_objects as go
        
        # CAMBIO PRINCIPAL: Usar predicciones del modelo ML con datos del usuario
        df_prediccion = df_prediccion_usuario.copy()
        
        # YA NO NECESITAS CALCULAR PROBABILIDADES MANUALMENTE
        # Las probabilidades ya vienen del modelo ML en 'probabilidad_tardia'
        
        total_ordenes = len(df_prediccion)
        ordenes_riesgo = len(df_prediccion[df_prediccion['probabilidad_tardia'] >= 0.5])
        porcentaje_riesgo = (ordenes_riesgo / total_ordenes * 100) if total_ordenes > 0 else 0

        col_vel, col_cards = st.columns([1, 2])

        with col_vel:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=porcentaje_riesgo,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Porcentaje de entregas en riesgo (ML)", 'font': {'size': 14}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "darkblue"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 30], 'color': '#D1FAE5'},
                        {'range': [30, 60], 'color': '#FEF3C7'},
                        {'range': [60, 100], 'color': '#FEE2E2'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                }
            ))

            fig_gauge.update_layout(paper_bgcolor="white", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        import streamlit.components.v1 as components

        with col_cards:
            # Verificar si existen las columnas necesarias para las cards
            if 'sucursal_asignada' in df_prediccion.columns and 'estado_cliente' in df_prediccion.columns:
                sucursales_stats = df_prediccion.groupby(['sucursal_asignada', 'estado_cliente']).agg({
                    'probabilidad_tardia': lambda x: sum(x >= 0.5),
                    'id_cliente': 'count' if 'id_cliente' in df_prediccion.columns else lambda x: len(x)
                }).reset_index()

                sucursales_stats.columns = ['sucursal', 'estado', 'entregas_riesgo', 'total_entregas']

                def get_color_indicator(entregas_riesgo):
                    if entregas_riesgo < 10:
                        return "⚪️"
                    elif entregas_riesgo <= 20:
                        return "🟡"
                    else:
                        return "⚪️"

                sucursales_stats['indicador'] = sucursales_stats['entregas_riesgo'].apply(get_color_indicator)
                sucursales_stats_sorted = sucursales_stats.sort_values('entregas_riesgo', ascending=False)

                # HTML y CSS mejorado para las cards
                cards_html = """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
                    
                    .cards-container {
                        display: flex;
                        overflow-x: auto;
                        gap: 16px;
                        padding: 16px 8px;
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        border-radius: 16px;
                        margin: 8px 0;
                        max-height: 320px;
                    }

                    .cards-container::-webkit-scrollbar {
                        height: 8px;
                    }

                    .cards-container::-webkit-scrollbar-track {
                        background: #f1f5f9;
                        border-radius: 4px;
                    }

                    .cards-container::-webkit-scrollbar-thumb {
                        background: linear-gradient(135deg, #cbd5e1, #94a3b8);
                        border-radius: 4px;
                    }

                    .modern-card {
                        min-width: 240px;
                        height: 280px;
                        background: #F8F6F070;
                        border-radius: 20px;
            
                        position: relative;
                        overflow: hidden;
                        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        padding: 0;
                    }

                    .modern-card:hover {
                        transform: translateY(-8px) rotateX(2deg);
                    }

                    .card-header {
                        height: 8px;
                        border-radius: 24px 24px 0 0;
                        position: relative;
                        overflow: hidden;
                    }

                    .card-header::after {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 100%;
                        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%);
                        animation: shimmer 3s infinite;
                    }

                    @keyframes shimmer {
                        0% { transform: translateX(-100%); }
                        100% { transform: translateX(100%); }
                    }

                    .logo-section {
                        padding: 20px 16px 16px 16px;
                        text-align: center;
                        position: relative;
                    }

                    .logo-circle {
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        margin: 0 auto 12px auto;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
                        position: relative;
                        overflow: hidden;
                    }

                    .logo-circle.high-risk {
                        background: linear-gradient(145deg, #dc2626, #b91c1c);
                        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
                    }

                    .logo-circle.medium-risk {
                        background: linear-gradient(145deg, #f59e0b, #d97706);
                        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
                    }

                    .logo-circle.low-risk {
                        background: linear-gradient(145deg, #10b981, #059669);
                        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
                    }

                    .logo-circle::before {
                        content: '';
                        position: absolute;
                        top: -50%;
                        left: -50%;
                        width: 200%;
                        height: 200%;
                        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
                        animation: rotate 4s linear infinite;
                    }

                    @keyframes rotate {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }

                    .logo-indicator {
                        font-size: 24px;
                        z-index: 1;
                        position: relative;
                        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
                    }

                    .store-name {
                        font-size: 16px;
                        font-weight: 700;
                        color: #1e293b;
                        margin-bottom: 6px;
                        letter-spacing: -0.3px;
                        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        line-height: 1.1;
                        min-height: 32px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }

                    .location-badge {
                        color: #64748b;
                        font-size: 12px;
                        font-weight: 500;
                        padding: 4px 12px;
                        border-radius: 12px;
                        display: inline-block;
                        margin-bottom: 16px;
                        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
                    }

                    .location-badge.high-risk {
                        background: linear-gradient(135deg, #fecaca, #fca5a5);
                    }

                    .location-badge.medium-risk {
                        background: linear-gradient(135deg, #fed7aa, #fdba74);
                    }

                    .location-badge.low-risk {
                        background: linear-gradient(135deg, #a7f3d0, #6ee7b7);
                    }

                    .number-section {
                        text-align: center;
                        padding: 16px;
                        position: relative;
                    }

                    .risk-number {
                        font-size: 48px;
                        font-weight: 900;
                        margin-bottom: 6px;
                        text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        line-height: 1;
                    }

                    .risk-label {
                        font-size: 12px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 6px;
                    }

                    .risk-label.high-risk {
                        color: #dc2626;
                    }

                    .risk-label.medium-risk {
                        color: #f59e0b;
                    }

                    .risk-label.low-risk {
                        color: #10b981;
                    }

                    .warning-icon {
                        animation: pulse 2s infinite;
                    }

                    @keyframes pulse {
                        0%, 100% { transform: scale(1); opacity: 1; }
                        50% { transform: scale(1.2); opacity: 0.8; }
                    }

                    .decorative-elements {
                        position: absolute;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        overflow: hidden;
                        top: 0;
                        left: 0;
                    }

                    .floating-circle {
                        position: absolute;
                        border-radius: 50%;
                        opacity: 0.1;
                    }

                    .floating-circle.circle-1 {
                        width: 100px;
                        height: 100px;
                        top: -50px;
                        right: -50px;
                        animation: float 6s ease-in-out infinite;
                    }

                    .floating-circle.circle-2 {
                        width: 60px;
                        height: 60px;
                        bottom: -30px;
                        left: -30px;
                        animation: float 4s ease-in-out infinite reverse;
                    }

                    .floating-circle.high-risk {
                        background: #dc2626;
                    }

                    .floating-circle.medium-risk {
                        background: #f59e0b;
                    }

                    .floating-circle.low-risk {
                        background: #10b981;
                    }

                    @keyframes float {
                        0%, 100% { transform: translateY(0px) rotate(0deg); }
                        50% { transform: translateY(-15px) rotate(180deg); }
                    }
                </style>

                <div class="cards-container">
                """

                for _, row in sucursales_stats_sorted.iterrows():
                    # Determinar el nivel de riesgo
                    if row['entregas_riesgo'] >= 20:
                        risk_level = 'high-risk'
                        risk_icon = ''
                    elif row['entregas_riesgo'] >= 10:
                        risk_level = 'medium-risk'
                        risk_icon = ''
                    else:
                        risk_level = 'low-risk'
                        risk_icon = ''

                    # Truncar nombre si es muy largo
                    nombre_display = row['sucursal']
                    if len(nombre_display) > 30:
                        nombre_display = nombre_display[:27] + '...'

                    card = f"""
                    <div class="modern-card">
                        <div class="card-header {risk_level}"></div>
                        
                        <div class="logo-section">
                            <div class="logo-circle {risk_level}">
                                <div class="logo-indicator">{row['indicador']}</div>
                            </div>
                            <div class="store-name">{nombre_display}</div>
                            <div class="location-badge {risk_level}">{row['estado']}</div>
                        </div>
                        
                        <div class="number-section">
                            <div class="risk-number">{int(row['entregas_riesgo'])}</div>
                            <div class="risk-label {risk_level}">
                                <span class="warning-icon">{risk_icon}</span>
                                En riesgo
                            </div>
                        </div>
                        
                        <div class="decorative-elements">
                            <div class="floating-circle circle-1 {risk_level}"></div>
                            <div class="floating-circle circle-2 {risk_level}"></div>
                        </div>
                    </div>
                    """
                    cards_html += card

                cards_html += "</div>"
                
                # Renderizar el HTML con altura reducida para que quepa en 320px
                components.html(cards_html, height=320, scrolling=True)
            else:
                st.info("Las columnas 'sucursal_asignada' y 'estado_cliente' no están disponibles en los datos para mostrar las tarjetas.")

        # Preparar columnas para mostrar - adaptable a diferentes datasets
        columnas_base = ['probabilidad_tardia', 'estatus_predicho']
        
        # Intentar incluir columnas comunes si existen
        columnas_comunes = [
            'orden_compra_timestamp', 'order_id', 'estado_cliente',
            'sucursal_asignada', 'dia_de_la_semana_entrega', 'tipo_dia_transportista'
        ]
        
        columnas_disponibles = [col for col in columnas_comunes if col in df_prediccion.columns]
        columnas_mostrar = columnas_disponibles + columnas_base
        
        # Si no hay columnas comunes, mostrar las primeras columnas del dataset + las predicciones
        if not columnas_disponibles:
            otras_columnas = [col for col in df_prediccion.columns 
                            if col not in columnas_base][:6]  # Primeras 6 columnas
            columnas_mostrar = otras_columnas + columnas_base

        df_display = df_prediccion[columnas_mostrar].copy()

        # Formatear columnas si existen
        if 'orden_compra_timestamp' in df_display.columns:
            df_display['orden_compra_timestamp'] = pd.to_datetime(df_display['orden_compra_timestamp']).dt.strftime('%Y-%m-%d')
        
        df_display['probabilidad_tardia'] = (df_display['probabilidad_tardia'] * 100).round(1)

        # Renombrar columnas de manera dinámica
        nuevos_nombres = {}
        for col in df_display.columns:
            if col == 'orden_compra_timestamp':
                nuevos_nombres[col] = 'Fecha Orden'
            elif col == 'order_id':
                nuevos_nombres[col] = 'Order ID'
            elif col == 'estado_cliente':
                nuevos_nombres[col] = 'Estado'
            elif col == 'sucursal_asignada':
                nuevos_nombres[col] = 'Sucursal'
            elif col == 'probabilidad_tardia':
                nuevos_nombres[col] = 'Riesgo (%)'
            elif col == 'estatus_predicho':
                nuevos_nombres[col] = 'Predicción'
            # Si no coincide con ninguno, mantener el nombre original
        
        df_display = df_display.rename(columns=nuevos_nombres)
        df_display = df_display.sort_values('Riesgo (%)', ascending=False)
        
        max_rows = 1000
        df_display_limited = df_display.head(max_rows)

        def color_fila_por_riesgo(row):
            if row['Riesgo (%)'] >= 70:
                return ['background-color: #FEE2E2'] * len(row)
            elif row['Riesgo (%)'] >= 40:
                return ['background-color: #FEF3C7'] * len(row)
            else:
                return ['background-color: #D1FAE5'] * len(row)

        styled_df = df_display_limited.style.apply(color_fila_por_riesgo, axis=1)
   
        # TABLA DENTRO DE UN EXPANDER IGUAL AL DE VISTA PREVIA
        with st.expander("👁️ Vista previa resultados del Modelo"):
            st.dataframe(
                styled_df, 
                use_container_width=True, 
                height=500,
                hide_index=True
            )
        
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')
        
        csv_data = convert_df_to_csv(df_display)
        
        st.download_button(
            label="Descargar Resultados (CSV)",
            data=csv_data,
            file_name=f"predicciones_entregas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    elif df_usuario is None:
        st.info("Por favor, carga una base de datos para comenzar con las predicciones")
    elif model is None:
        st.error("El modelo no se pudo entrenar. Verifica que el archivo 'BaseDeDatosFinal_ajustado2.parquet' esté disponible")
    else:
        st.warning("Ocurrió un problema inesperado. Por favor, verifica los datos y el modelo.")



######
#TAB 3 - CALCULADORA DE COSTOS POR RETRASOS
######
with tab3:
    
    
    # Layout principal: Tabla + Resultados + Calculadora
    col_table, col_results, col_calc = st.columns([1.5, 1, 1], gap="large")
    
    # TABLA SIMPLIFICADA (solo Estado y Total Días de Retraso) - PRIMERO
    with col_table:
        st.markdown("""
            <div class="section-title">📋 Detalle de Retrasos por Estado</div>
        """, unsafe_allow_html=True)
        
        # Calcular tabla de retrasos por estado (solo las columnas necesarias)
        estados_disponibles = sorted(df_table_filtered['estado_cliente'].dropna().unique())
        estados_retrasos = []
        dias_ideal = 3  # Tiempo de entrega ideal en días
        
        for estado in estados_disponibles:
            df_estado = df_table_filtered[df_table_filtered['estado_cliente'] == estado]
            df_tardias_estado = df_estado[df_estado['estatus_de_entrega'] == 'Tardia']
            
            if len(df_tardias_estado) > 0:
                # Calcular días de retraso
                dias_retraso = (df_tardias_estado['tiempo_de_entrega'] - dias_ideal).clip(lower=0)
                total_dias_retraso = dias_retraso.sum()
                
                estados_retrasos.append({
                    'Estado': estado,
                    'Total Días Retraso': int(total_dias_retraso)
                })
        
        # Convertir a DataFrame y ordenar por total días de retraso
        df_retrasos = pd.DataFrame(estados_retrasos)
        df_retrasos = df_retrasos.sort_values('Total Días Retraso', ascending=False)
        
        # Mostrar tabla simplificada
        st.dataframe(
            df_retrasos,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn("Estado", width=200),
                "Total Días Retraso": st.column_config.NumberColumn("Total Días Retraso", width=200)
            }
        )

    # CALCULADORA - TERCERO
    with col_calc:
        
        # Selectbox para elegir estado
        estado_seleccionado = st.selectbox(
            "Seleccionar Estado",
            estados_disponibles,
            index=0 if estados_disponibles else None
        )
        
        # Input para costo por día
        costo_por_dia = st.number_input(
            "Costo por Día ($)",
            min_value=0.0,
            value=1200.0,
            step=10.0,
            format="%.2f",
            key="costo_por_dia"
        )

    # RESULTADOS - SEGUNDO
    with col_results:
        
        # Calcular estadísticas del estado seleccionado
        if estado_seleccionado:
            df_estado_calc = df_table_filtered[df_table_filtered['estado_cliente'] == estado_seleccionado]
            
            # Filtrar solo entregas tardías
            df_tardias = df_estado_calc[df_estado_calc['estatus_de_entrega'] == 'Tardia']
            
            if len(df_tardias) > 0:
                # Calcular días de retraso acumulados (asumiendo que el tiempo de entrega ideal es 3 días)
                dias_ideal = 3
                df_tardias_calc = df_tardias.copy()
                df_tardias_calc['dias_retraso'] = df_tardias_calc['tiempo_de_entrega'] - dias_ideal
                df_tardias_calc['dias_retraso'] = df_tardias_calc['dias_retraso'].clip(lower=0)
                
                total_dias_retraso = df_tardias_calc['dias_retraso'].sum()
                # Obtener costo por día del input de la calculadora
                if 'costo_por_dia' in st.session_state:
                    costo_por_dia = st.session_state.costo_por_dia
                else:
                    costo_por_dia = 1200.0  # Valor por defecto
                
                # Calcular costo total
                costo_total = total_dias_retraso * costo_por_dia
                
                # Formatear el costo total de forma abreviada
                if costo_total >= 1_000_000:
                    costo_formateado = f"${costo_total/1_000_000:.1f}M"
                elif costo_total >= 1_000:
                    costo_formateado = f"${costo_total/1_000:.1f}K"
                else:
                    costo_formateado = f"${costo_total:.0f}"
                
                # Mostrar los 3 resultados específicos
                st.markdown(f"""
                    <div style="background-color: #FFFBEB; border-left: 6px solid #F59E0B; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <div style="font-size: 14px; color: #374151;">Total Días de Retraso</div>
                        <div style="font-size: 24px; font-weight: bold; color: #F59E0B;">{total_dias_retraso:,.0f} días</div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div style="background-color: #FEE2E2; border-left: 6px solid #DC2626; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <div style="font-size: 14px; color: #374151;">Costo Total Estimado</div>
                        <div style="font-size: 28px; font-weight: bold; color: #DC2626;">{costo_formateado}</div>
                    </div>
                """, unsafe_allow_html=True)
                
            else:
                st.info("No hay entregas tardías registradas para este estado.")



######
#TAB 4
######
with tab4:
    st.subheader("Ruta real y conteo de calles")

    # coordenadas dummy (lon, lat)
    ORIGIN = (-100.350, 25.683)
    DEST   = (-100.300, 25.700)

    # crea el grafo desde el punto de origen
    G = ox.graph_from_point((ORIGIN[1], ORIGIN[0]), dist=5000, network_type='drive')

    # encuentra los nodos más cercanos en el grafo
    orig_node = ox.distance.nearest_nodes(G, X=ORIGIN[0], Y=ORIGIN[1])
    dest_node = ox.distance.nearest_nodes(G, X=DEST[0], Y=DEST[1])

    # calcula la ruta más corta
    route = nx.shortest_path(G, orig_node, dest_node, weight='length')

    # extrae los nombres de las calles
    calles = []
    for u, v in zip(route[:-1], route[1:]):
        data = G.get_edge_data(u, v)[0]
        name = data.get('name', 'sin_nombre')
        if isinstance(name, list):
            calles.extend(name)
        else:
            calles.append(name)

    calles_unicas = set(calles)

    # crea el mapa con altura más baja
    m = folium.Map(location=[(ORIGIN[1]+DEST[1])/2, (ORIGIN[0]+DEST[0])/2], zoom_start=13)
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    folium.PolyLine(coords, color='blue', weight=4, opacity=0.7).add_to(m)
    folium.Marker((ORIGIN[1], ORIGIN[0]), popup="Origen", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker((DEST[1], DEST[0]), popup="Destino", icon=folium.Icon(color="red")).add_to(m)

    # usar columnas para centrar el mapa
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st_folium(m, width=600, height=350)

