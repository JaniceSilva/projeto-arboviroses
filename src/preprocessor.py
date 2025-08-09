import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataPreprocessor:
    def __init__(self):
        self.scalers = {}
    
    def clean_data(self, df):
        """Limpeza e tratamento de dados"""
        # Verificar colunas essenciais
        required_cols = ['data', 'municipio']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Coluna obrigatória '{col}' não encontrada")
        
        # Preencher valores ausentes
        climate_cols = ['temperatura', 'umidade', 'precipitacao']
        case_cols = ['casos_dengue', 'casos_zika', 'casos_chikungunya']
        
        for col in climate_cols:
            if col in df.columns:
                df[col].fillna(df[col].mean(), inplace=True)
            else:
                df[col] = np.nan
                df[col].fillna(df[col].mean(), inplace=True)
        
        for col in case_cols:
            if col in df.columns:
                df[col].fillna(0, inplace=True)
            else:
                df[col] = 0
        
        # Remover outliers
        for col in case_cols:
            q1 = df[col].quantile(0.05)
            q3 = df[col].quantile(0.95)
            df[col] = np.clip(df[col], q1, q3)
        
        return df

    def create_features(self, df):
        """Engenharia de features"""
        # Converter data
        df['data'] = pd.to_datetime(df['data'])
        
        # Features temporais
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['dia_do_ano'] = df['data'].dt.dayofyear
        df['semana_epidemiologica'] = df['data'].dt.isocalendar().week
        
        # Features cíclicas
        df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
        df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
        
        # Features de atraso (lag) para casos
        case_cols = ['casos_dengue', 'casos_zika', 'casos_chikungunya']
        for col in case_cols:
            for lag in [7, 14, 21, 28]:  # Lags semanais
                df[f'{col}_lag_{lag}'] = df.groupby('municipio')[col].shift(lag)
            
            # Média móvel
            df[f'{col}_media_movel_4'] = df.groupby('municipio')[col].transform(
                lambda x: x.rolling(4, min_periods=1).mean()
            )
        
        return df

    def normalize_data(self, df):
        """Normalização dos dados numéricos"""
        # Colunas para normalizar
        numeric_cols = ['temperatura', 'umidade', 'precipitacao', 'dia_do_ano']
        
        for col in numeric_cols:
            if col in df.columns:
                # Preencher valores nulos
                if df[col].isnull().any():
                    df[col].fillna(df[col].mean(), inplace=True)
                
                # Normalizar
                scaler = StandardScaler()
                df[col] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
        
        return df

    def preprocess(self, df):
        """Pipeline completo de pré-processamento"""
        logging.info("Iniciando pré-processamento de dados")
        
        # Etapas de processamento
        df = self.clean_data(df)
        df = self.create_features(df)
        df = self.normalize_data(df)
        
        # Remover valores nulos resultantes de lags
        df = df.dropna()
        
        logging.info(f"Pré-processamento concluído: {df.shape[0]} registros")
        return df