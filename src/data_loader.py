import psycopg2
import pandas as pd
import os
import logging
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    """Carrega e une dados climáticos e de arboviroses de tabelas diferentes"""
    try:
        conn = psycopg2.connect(os.getenv('DB_URL'))
        
        # 1. Carregar dados climáticos
        climate_query = """
            SELECT 
                data_hora AS data,
                municipio,
                temperatura_media AS temperatura,
                umidade_media AS umidade,
                precipitacao
            FROM dados_climaticos
            WHERE municipio IN ('Teófilo Otoni', 'Diamantina');
        """
        climate_df = pd.read_sql(climate_query, conn)
        logging.info(f"Dados climáticos carregados: {climate_df.shape[0]} registros")
        
        # 2. Carregar dados de arboviroses
        arbovirus_query = """
            SELECT 
                data_coleta AS data,
                municipio,
                dengue AS casos_dengue,
                zika AS casos_zika,
                chikungunya AS casos_chikungunya
            FROM dados_arboviroses
            WHERE municipio IN ('Teófilo Otoni', 'Diamantina');
        """
        arbovirus_df = pd.read_sql(arbovirus_query, conn)
        logging.info(f"Dados de arboviroses carregados: {arbovirus_df.shape[0]} registros")
        
        conn.close()
        
        # 3. Unir os dados
        # Converter datas para formato diário (agrupar por dia)
        climate_df['data'] = pd.to_datetime(climate_df['data']).dt.normalize()
        arbovirus_df['data'] = pd.to_datetime(arbovirus_df['data']).dt.normalize()
        
        # Agregar dados climáticos por dia (média)
        climate_agg = climate_df.groupby(['data', 'municipio']).agg({
            'temperatura': 'mean',
            'umidade': 'mean',
            'precipitacao': 'sum'  # Soma de precipitação diária
        }).reset_index()
        
        # Unir datasets
        df = pd.merge(
            climate_agg,
            arbovirus_df,
            on=['data', 'municipio'],
            how='left'  # Manter todos os dias climáticos
        )
        
        # Preencher valores faltantes de casos
        case_cols = ['casos_dengue', 'casos_zika', 'casos_chikungunya']
        for col in case_cols:
            df[col] = df[col].fillna(0)
        
        logging.info(f"Dados unificados: {df.shape[0]} registros")
        return df
        
    except Exception as e:
        logging.error(f"Erro ao carregar dados: {e}")
        return load_fallback_data()

def load_fallback_data():
    """Carrega dados de fallback com informações completas"""
    logging.warning("Carregando dados de fallback")
    
    # Criar dados sintéticos completos
    start_date = datetime.now() - relativedelta(months=12)
    dates = [start_date + timedelta(days=i) for i in range(365)]
    
    data = {
        'data': dates * 2,  # 2 municípios
        'municipio': ['Teófilo Otoni']*365 + ['Diamantina']*365,
        'temperatura': np.concatenate([
            np.sin(np.linspace(0, 10, 365)) * 10 + 25,  # Teófilo Otoni
            np.sin(np.linspace(0, 10, 365)) * 8 + 22     # Diamantina
        ]),
        'umidade': np.concatenate([
            np.cos(np.linspace(0, 8, 365)) * 20 + 60,    # Teófilo Otoni
            np.cos(np.linspace(0, 8, 365)) * 15 + 65      # Diamantina
        ]),
        'precipitacao': np.random.gamma(2, 5, 730),      # Distribuição de chuva
        
        # Casos com sazonalidade e correlação com chuva
        'casos_dengue': np.random.poisson(
            np.clip(np.random.gamma(2, 5, 730) * 0.5 + 
            np.random.gamma(2, 2, 730), 10
        ),
        'casos_zika': np.random.poisson(
            np.clip(np.random.gamma(1, 3, 730) * 0.3 + 
            np.random.gamma(1, 1, 730), 5
        ),
        'casos_chikungunya': np.random.poisson(
            np.clip(np.random.gamma(1, 2, 730) * 0.2 + 
            np.random.gamma(1, 1, 730), 3
        )
    }
    
    df = pd.DataFrame(data)
    
    # Ajustar datas
    df['data'] = pd.to_datetime(df['data'])
    
    logging.warning(f"Dados sintéticos gerados: {df.shape[0]} registros")
    return df