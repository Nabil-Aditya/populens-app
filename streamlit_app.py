import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="PopuLens - Analisis Demografi Global",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .country-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi cache untuk API World Bank
@st.cache_data(ttl=7200)
def get_demographic_data(indicator, start_year=2010, end_year=2022):
    """Fetch data dari World Bank API dengan range tahun"""
    url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator}"
    params = {
        'date': f'{start_year}:{end_year}',
        'format': 'json',
        'per_page': 20000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                records = []
                for item in data[1]:
                    if item['value'] is not None and item['countryiso3code']:
                        records.append({
                            'country': item['country']['value'],
                            'code': item['countryiso3code'],
                            'value': float(item['value']),
                            'year': int(item['date'])
                        })
                return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error: {e}")
    return pd.DataFrame()

# Header
st.markdown('<h1 class="main-header">👥 PopuLens</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:1.2rem; color:#666;">Platform Analisis Demografi Global - Real-time Data Kelahiran & Kematian</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://em-content.zobj.net/source/twitter/376/globe-showing-asia-australia_1f30f.png", width=80)
    st.title("🎛️ Panel Kontrol")
    
    # Time range selector
    st.subheader("📅 Rentang Waktu")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox("Dari", range(2010, 2023), index=0)
    with col2:
        end_year = st.selectbox("Sampai", range(2010, 2023), index=12)
    
    if start_year > end_year:
        st.error("Tahun awal harus lebih kecil dari tahun akhir!")
        st.stop()
    
    # Visualization mode
    st.subheader("📊 Mode Visualisasi")
    viz_mode = st.radio(
        "Pilih Mode",
        ["🗺️ Peta Global", "📈 Tren Waktu", "🔍 Analisis Negara", "⚖️ Komparasi"]
    )
    
    # Country selector for specific analysis
    if viz_mode in ["📈 Tren Waktu", "🔍 Analisis Negara"]:
        country_list = ["Indonesia", "China", "India", "United States", "Brazil", 
                       "Nigeria", "Japan", "Germany", "United Kingdom", "France"]
        selected_countries = st.multiselect(
            "Pilih Negara",
            country_list,
            default=["Indonesia", "China", "India"]
        )
    
    # Indicator selector
    st.subheader("📍 Indikator")
    indicator_type = st.selectbox(
        "Pilih Data",
        ["Birth Rate", "Death Rate", "Natural Increase", "Population Growth"]
    )
    
    st.divider()
    st.info("💡 **Data Source:** World Bank Open Data API")
    st.caption("📊 Update terakhir: Setiap 6 jam")

# Load data
with st.spinner("🔄 Mengambil data dari World Bank..."):
    birth_df = get_demographic_data('SP.DYN.CBRT.IN', start_year, end_year)
    death_df = get_demographic_data('SP.DYN.CDRT.IN', start_year, end_year)
    pop_growth_df = get_demographic_data('SP.POP.GROW', start_year, end_year)

if birth_df.empty or death_df.empty:
    st.error("❌ Gagal memuat data. Silakan refresh halaman.")
    st.stop()

# Merge datasets
df = birth_df.merge(death_df, on=['country', 'code', 'year'], suffixes=('_birth', '_death'))
if not pop_growth_df.empty:
    df = df.merge(pop_growth_df[['code', 'year', 'value']], on=['code', 'year'], how='left')
    df.rename(columns={'value': 'pop_growth'}, inplace=True)

df['natural_increase'] = df['value_birth'] - df['value_death']
df.columns = df.columns.str.replace('value_birth', 'birth_rate')
df.columns = df.columns.str.replace('value_death', 'death_rate')

# Get latest year data for metrics
latest_year = df['year'].max()
latest_data = df[df['year'] == latest_year]

# Key Metrics
st.subheader("📊 Statistik Global Terbaru ({})".format(latest_year))
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_birth = latest_data['birth_rate'].mean()
    st.metric(
        "🍼 Avg. Birth Rate",
        f"{avg_birth:.2f}‰",
        help="Rata-rata kelahiran per 1,000 penduduk"
    )

with col2:
    avg_death = latest_data['death_rate'].mean()
    st.metric(
        "⚰️ Avg. Death Rate",
        f"{avg_death:.2f}‰",
        help="Rata-rata kematian per 1,000 penduduk"
    )

with col3:
    avg_increase = latest_data['natural_increase'].mean()
    delta_color = "normal" if avg_increase > 0 else "inverse"
    st.metric(
        "📈 Natural Increase",
        f"{avg_increase:.2f}‰",
        delta=f"{avg_increase:.2f}",
        delta_color=delta_color
    )

with col4:
    total_countries = latest_data['country'].nunique()
    st.metric(
        "🌍 Total Countries",
        f"{total_countries}",
        help="Negara dengan data tersedia"
    )

st.divider()

# Visualization berdasarkan mode
if viz_mode == "🗺️ Peta Global":
    st.subheader(f"🗺️ Peta Global - {latest_year}")
    
    tab1, tab2, tab3 = st.tabs(["🍼 Birth Rate", "⚰️ Death Rate", "📈 Natural Increase"])
    
    with tab1:
        fig_birth = px.choropleth(
            latest_data,
            locations="code",
            color="birth_rate",
            hover_name="country",
            hover_data={'birth_rate': ':.2f', 'code': False},
            color_continuous_scale="YlGnBu",
            title=f"Birth Rate per 1,000 population ({latest_year})",
            labels={'birth_rate': 'Birth Rate (‰)'}
        )
        fig_birth.update_geos(showcountries=True, countrycolor="lightgray")
        fig_birth.update_layout(height=600, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_birth, use_container_width=True)
    
    with tab2:
        fig_death = px.choropleth(
            latest_data,
            locations="code",
            color="death_rate",
            hover_name="country",
            hover_data={'death_rate': ':.2f', 'code': False},
            color_continuous_scale="OrRd",
            title=f"Death Rate per 1,000 population ({latest_year})",
            labels={'death_rate': 'Death Rate (‰)'}
        )
        fig_death.update_geos(showcountries=True, countrycolor="lightgray")
        fig_death.update_layout(height=600, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_death, use_container_width=True)
    
    with tab3:
        fig_increase = px.choropleth(
            latest_data,
            locations="code",
            color="natural_increase",
            hover_name="country",
            hover_data={
                'birth_rate': ':.2f',
                'death_rate': ':.2f',
                'natural_increase': ':.2f',
                'code': False
            },
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            title=f"Natural Increase ({latest_year})",
            labels={'natural_increase': 'Natural Increase (‰)'}
        )
        fig_increase.update_geos(showcountries=True, countrycolor="lightgray")
        fig_increase.update_layout(height=600, margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_increase, use_container_width=True)

elif viz_mode == "📈 Tren Waktu":
    st.subheader("📈 Analisis Tren Historis")
    
    if not selected_countries:
        st.warning("⚠️ Pilih minimal 1 negara di sidebar!")
    else:
        trend_data = df[df['country'].isin(selected_countries)]
        
        # Line chart untuk birth rate
        fig_trend = go.Figure()
        for country in selected_countries:
            country_data = trend_data[trend_data['country'] == country]
            fig_trend.add_trace(go.Scatter(
                x=country_data['year'],
                y=country_data['birth_rate'],
                mode='lines+markers',
                name=f"{country} (Birth)",
                line=dict(width=2)
            ))
            fig_trend.add_trace(go.Scatter(
                x=country_data['year'],
                y=country_data['death_rate'],
                mode='lines+markers',
                name=f"{country} (Death)",
                line=dict(dash='dash', width=2)
            ))
        
        fig_trend.update_layout(
            title="Birth Rate vs Death Rate Over Time",
            xaxis_title="Year",
            yaxis_title="Rate per 1,000 population",
            hovermode='x unified',
            height=500
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Natural increase trend
        fig_ni = px.line(
            trend_data,
            x='year',
            y='natural_increase',
            color='country',
            title="Natural Increase Trend",
            labels={'natural_increase': 'Natural Increase (‰)', 'year': 'Year'}
        )
        fig_ni.update_traces(mode='lines+markers')
        fig_ni.update_layout(height=400)
        st.plotly_chart(fig_ni, use_container_width=True)

elif viz_mode == "🔍 Analisis Negara":
    st.subheader("🔍 Analisis Detail per Negara")
    
    if not selected_countries:
        st.warning("⚠️ Pilih minimal 1 negara di sidebar!")
    else:
        for country in selected_countries:
            country_data = df[df['country'] == country].sort_values('year')
            
            with st.expander(f"🌍 {country}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                latest_country = country_data[country_data['year'] == latest_year].iloc[0]
                
                with col1:
                    st.metric("🍼 Birth Rate", f"{latest_country['birth_rate']:.2f}‰")
                with col2:
                    st.metric("⚰️ Death Rate", f"{latest_country['death_rate']:.2f}‰")
                with col3:
                    st.metric("📈 Natural Increase", f"{latest_country['natural_increase']:.2f}‰")
                
                # Mini sparkline
                fig_spark = go.Figure()
                fig_spark.add_trace(go.Scatter(
                    x=country_data['year'],
                    y=country_data['birth_rate'],
                    fill='tozeroy',
                    name='Birth',
                    line=dict(color='#667eea')
                ))
                fig_spark.add_trace(go.Scatter(
                    x=country_data['year'],
                    y=country_data['death_rate'],
                    fill='tozeroy',
                    name='Death',
                    line=dict(color='#f093fb')
                ))
                fig_spark.update_layout(
                    height=250,
                    margin=dict(l=0, r=0, t=20, b=0),
                    showlegend=True,
                    hovermode='x unified'
                )
                st.plotly_chart(fig_spark, use_container_width=True)

else:  # Komparasi
    st.subheader("⚖️ Komparasi Negara")
    
    # Top 10 highest birth rate
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔝 Top 10 Highest Birth Rate")
        top_birth = latest_data.nlargest(10, 'birth_rate')[['country', 'birth_rate']]
        fig_top_birth = px.bar(
            top_birth,
            x='birth_rate',
            y='country',
            orientation='h',
            color='birth_rate',
            color_continuous_scale='Greens',
            labels={'birth_rate': 'Birth Rate (‰)'}
        )
        fig_top_birth.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_top_birth, use_container_width=True)
    
    with col2:
        st.markdown("#### 🔝 Top 10 Highest Death Rate")
        top_death = latest_data.nlargest(10, 'death_rate')[['country', 'death_rate']]
        fig_top_death = px.bar(
            top_death,
            x='death_rate',
            y='country',
            orientation='h',
            color='death_rate',
            color_continuous_scale='Reds',
            labels={'death_rate': 'Death Rate (‰)'}
        )
        fig_top_death.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_top_death, use_container_width=True)
    
    # Scatter plot
    st.markdown("#### 📊 Birth Rate vs Death Rate Correlation")
    fig_scatter = px.scatter(
        latest_data,
        x='death_rate',
        y='birth_rate',
        size='natural_increase',
        color='natural_increase',
        hover_name='country',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        labels={
            'death_rate': 'Death Rate (‰)',
            'birth_rate': 'Birth Rate (‰)',
            'natural_increase': 'Natural Increase (‰)'
        }
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

# Data Table
st.divider()
st.subheader("📋 Data Explorer")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    year_filter = st.selectbox("Filter Tahun", ["All"] + sorted(df['year'].unique().tolist(), reverse=True))
with col2:
    sort_column = st.selectbox("Sort By", ['country', 'birth_rate', 'death_rate', 'natural_increase'])
with col3:
    sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

# Apply filters
display_df = df.copy()
if year_filter != "All":
    display_df = display_df[display_df['year'] == year_filter]

display_df = display_df.sort_values(
    by=sort_column,
    ascending=(sort_order == "Ascending")
)

# Show table
st.dataframe(
    display_df[['country', 'year', 'birth_rate', 'death_rate', 'natural_increase']].style.format({
        'birth_rate': '{:.2f}',
        'death_rate': '{:.2f}',
        'natural_increase': '{:.2f}'
    }).background_gradient(subset=['natural_increase'], cmap='RdYlGn'),
    use_container_width=True,
    height=400
)

# Download
csv_data = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Data (CSV)",
    data=csv_data,
    file_name=f'populens_data_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>PopuLens</strong> - Global Demographic Analysis Platform</p>
    <p>Data Source: World Bank Open Data API | Updates: Every 6 hours</p>
    <p>Birth Rate & Death Rate measured per 1,000 population</p>
    <p>Natural Increase = Birth Rate - Death Rate</p>
</div>
""", unsafe_allow_html=True)
