import streamlit as st
import geopandas as gpd
import pandas as pd
import fiona
from fiona.drvsupport import supported_drivers
import folium
from folium import Map, FeatureGroup, Marker, LayerControl, Popup
from streamlit_folium import folium_static
from folium import Choropleth, GeoJson, plugins
from folium import GeoJson
from branca.element import MacroElement
from jinja2 import Template
import branca
from shapely.ops import unary_union
import os
from shapely import wkt
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from PIL import Image
import shutil

# Copia o arquivo dos trechos MT concatenados para a pasta do GITHUB
# src = r'C:\Projetos\2022_23_LIGHT_Sust_Concessao\Fase 1\3 - Resultados\Delos\19-06-2024\Concat\LI_REDE_PF_TRECHO_MT_concatenado.pkl'
# dst = r'C:\Users\leosy\OneDrive\Documentos\GitHub\2023_Light_Dash\Dados\LINHAS\LI_REDE_PF_TRECHO_MT_concatenado.pkl'
# shutil.copyfile(src, dst)

# Função para carregar os dados dos trechos dos alimentadores.
@st.cache_data
def load_data():
    resultados_fme = pd.read_pickle('LI_REDE_PF_TRECHO_MT_concatenado.pkl')
    resultados_fme = resultados_fme[['STATUSIN','CODIGO','COMPRIME','geometry','Nome_Subpasta']]
    resultados_fme = resultados_fme.rename(columns={'Nome_Subpasta':'LINHA'})
    escopo = pd.read_excel(r'ALIM VALIDADOS - 09.05.2024.xlsx',header=1,usecols='B,C,E',sheet_name='DADOS')
    resultados_fme = resultados_fme.merge(escopo,how='left',left_on='LINHA',right_on='ALIMENTADOR')
    resultados_fme = resultados_fme.fillna('-')
    
    return resultados_fme


# Leitura das áreas de riscos
shp_AR = gpd.read_file(r'ASRO.shp')

# Definição de diferentes tipos de mapas base
basemaps = {
    'Google Maps': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Maps'
    ),
    'Google Satellite': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite'
    ),
    'Google Terrain': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Terrain'
    ),
    'Google Satellite Hybrid': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite'
    ),
    'Esri Satellite': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite'
    ),
    'CartoDB positron': folium.TileLayer(
        tiles='CartoDB positron',
        attr='CartoDB',
        name='Light Map'
    )
}

# Configuração da página do Streamlit
st.set_page_config(layout="wide")

# Carrega a imagem do logotipo e exibe no topo da página
image = Image.open(r'logo.png')
col1, col2, col3 = st.columns(3)
with col2:
    st.image(image)

# Adiciona o cabeçalho e o subtítulo
st.divider()
st.markdown("<h1 style='text-align: center; color: grey;'>LIGHT - Inventário de Ativos</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: black;'>Ativos Levantados em Campo </h2>", unsafe_allow_html=True)
st.divider()

# Autenticação do usuário utilizando o Streamlit Authenticator

# Carregamento dos dados de credenciais de um arquivo YAML
with open(r'Credencias.yml') as file:
    config = yaml.load(file, Loader=SafeLoader)


# Criação do objeto de autenticação
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)


# Renderização do widget de login
name, authentication_status, username = authenticator.login('Login', 'main')

# Verifica se a autenticação foi bem-sucedida
if authentication_status:
    authenticator.logout('Logout', 'main')
        
    st.write(f'Welcome *{name}*')

    # Criação das abas do Streamlit
    tab1, tab2 = st.tabs(["Painel Gerencial", "Mapa - Levantamento em Campo"])

    # Conteúdo da aba "Painel Gerencial"
    with tab1:
        st.title('Dashboard - Inventário de Ativos')
        st.markdown('https://app.powerbi.com/groups/me/reports/47e643db-3236-4b89-8250-73aa0384c51d/ReportSection?ctid=0c6c23de-546b-45ff-811a-a88cc514ae5f&experience=power-bi',unsafe_allow_html=True)

    # Conteúdo da aba "Mapas"
    with tab2:
        # Carrega os dados
        resultados_fme = load_data()

        # Adiciona um espaço em branco para mover o select box para a direita
        st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction: row-reverse}</style>', unsafe_allow_html=True)

        # Criação do select box para selecionar a "Regional"
        sel_regioes = resultados_fme['REGIONAL'].unique().astype('str').tolist()
        all_regioes = sel_regioes.copy()
        all_regioes.append('Todos')
        regional = st.multiselect("Selecione uma ou mais regiões:", all_regioes, placeholder='Selecione a regional ...')
        if "Todos" in regional:
            regional = sel_regioes
        elif regional == []:
            regional = sel_regioes

        regiao_df = resultados_fme[resultados_fme['REGIONAL'].isin(regional)]

        # Mapeamento de status para cores
        status_colors = {
            'N': 'gray',
            'D': 'red',
            'U': 'blue',
            'I': 'green',
        }

        # Adiciona uma coluna com as cores correspondentes aos status
        regiao_df['cor'] = resultados_fme['STATUSIN'].map(status_colors)

        # Criação do select box para selecionar a "Subestação"
        sel_setd = resultados_fme['SUBESTAÇÃO'].unique().astype('str').tolist()
        all_setd = sel_setd.copy()
        all_setd.append('Todos')
        subestacao = st.multiselect("Selecione uma ou mais subestações:", regiao_df[regiao_df['REGIONAL'].isin(regional)]['SUBESTAÇÃO'].unique(), placeholder='Selecione a subestação ...')
        if "Todos" in subestacao:
            subestacao = sel_setd
        elif subestacao == []:
            subestacao = sel_setd

        regiao_df = regiao_df[regiao_df['SUBESTAÇÃO'].isin(subestacao)]
  
        # Criação do select box para selecionar o "Alimentador"
        sel_linha = resultados_fme['LINHA'].unique().astype('str').tolist()
        all_linha = sel_linha.copy()
        all_linha.append('Todos')
        linha = st.multiselect("Selecione uma ou mais linhas:", regiao_df[regiao_df['SUBESTAÇÃO'].isin(subestacao)]['LINHA'].unique(), placeholder='Selecione a linha ...')
        if "Todos" in linha:
            linha = sel_linha
        elif linha == []:
            linha = sel_linha

        regiao_df = regiao_df[regiao_df['LINHA'].isin(linha)]

        # Criação do select box para selecionar o "Status"
        sel_status = resultados_fme['STATUSIN'].unique().astype('str').tolist()
        all_status = sel_status.copy()
        all_status.append('Todos')
        status = st.multiselect("Selecione um ou mais STATUSIN:", regiao_df[regiao_df['LINHA'].isin(linha)]['STATUSIN'].unique(), placeholder='Selecione o STATUSIN ...')
        if "Todos" in status:
            status = sel_status
        elif status == []:
            status = sel_status

        regiao_df = regiao_df[regiao_df['STATUSIN'].isin(status)]


        with st.spinner("Carregando mapa..."):
            # Calcula o centróide para centralizar o mapa
            centroide = regiao_df.to_crs(22182).centroid.to_crs(4326).iloc[[0]]
            mapa = folium.Map(location=[centroide.y, centroide.x], zoom_start=13)

            # Adicionar basemaps ao mapa
            for name, tile_layer in basemaps.items():
                tile_layer.add_to(mapa)

            # Adição de regiões com diferentes formas e cores utilizando arquivos shape
            colors = ['orange']
            for name, shp_data, color in zip(['ASRO'], [shp_AR], colors):
                folium.Choropleth(geo_data=shp_data, fill_color='pink', name=name).add_to(mapa)

            # Template HTML para a legenda
            legend_html = """
            {%macro html(this,kwargs)%}
            <div id='maplegend' class='maplegend' 
                style='position: fixed; z-index: 9998; background-color: rgba(255, 255, 255, 0.5);
                bottom: 12px; left: 870px; width: 120px; height: 110px; font-size: 10.5px; border: 1px solid gray; border-radius: 6px;'>
            <a style = "color: black; margin-left: 30px;"<><b>Legenda</b></a>     
            <div class='legend-scale'>
            <ul class='legend-labels' style="list-style-type: none; padding: 0; margin: 0;">
                <li><a style='color: gray; margin-left: 2px;'>&FilledSmallSquare; </a> N - Não Inventariado </li>
                <li><a style='color: red; margin-left: 2px;'>&FilledSmallSquare; </a> D - Deletado </li>
                <li><a style='color: blue; margin-left: 2px;'>&FilledSmallSquare; </a> U - Atualizado </li>
                <li><a style='color: green; margin-left: 2px;'>&FilledSmallSquare; </a> I - Inserido </li>
                <li><a style='color: pink; margin-left: 2px;'>&FilledSmallSquare; </a>Áreas de Risco </li>
            </ul>
            </div>
            {% endmacro %}
            """

            # Adiciona a legenda HTML ao mapa
            macro = branca.element.MacroElement()
            macro._template = branca.element.Template(legend_html)
            mapa.add_child(macro)

            # Adicionar GeoJson ao mapa com base na coluna de cor
            GeoJson(regiao_df, style_function=lambda feature: {'color': feature['properties']['cor'], 'weight': 2},name='ALIMENTADOR').add_to(mapa)

        # Adiciona controle de camadas ao mapa
        folium.LayerControl().add_to(mapa)

        # Adiciona o controle de tela cheia
        plugins.Fullscreen().add_to(mapa)

        # Exibe o mapa na aplicação Streamlit
        folium_static(mapa, width=1000, height=600)

        # Nome do arquivo para ser salvo
        nome_arquivo = st.text_input("Nome para download do mapa em HTML:") + '.html'
        # Botão para baixar o mapa como HTML
        if nome_arquivo:
            st.download_button(
                label="Download",
                data=mapa.get_root().render(),
                file_name=os.path.join(nome_arquivo),
                key="download_mapa_html"
                )

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
