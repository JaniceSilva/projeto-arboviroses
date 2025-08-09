from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_dashboard(df, predictions, alerts):
    app = Dash(__name__)
    
    # Estilos
    styles = {
        'container': {
            'padding': '20px',
            'fontFamily': 'Arial, sans-serif'
        },
        'header': {
            'backgroundColor': '#f8f9fa',
            'padding': '20px',
            'borderRadius': '5px',
            'marginBottom': '20px'
        },
        'graph-container': {
            'backgroundColor': '#ffffff',
            'padding': '15px',
            'borderRadius': '5px',
            'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
            'marginBottom': '20px'
        }
    }
    
    app.layout = html.Div(style=styles['container'], children=[
        html.Div(style=styles['header'], children=[
            html.H1("Sistema de Previsão de Arboviroses", style={'margin': '0'}),
            html.P("Monitoramento e alerta para dengue, zika e chikungunya")
        ]),
        
        # Filtros
        html.Div([
            html.Div([
                html.Label("Município:"),
                dcc.Dropdown(
                    id='municipio-dropdown',
                    options=[{'label': m, 'value': m} for m in df['municipio'].unique()],
                    value='Teófilo Otoni'
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
            
            html.Div([
                html.Label("Período:"),
                dcc.DatePickerRange(
                    id='date-picker',
                    min_date_allowed=df['data'].min(),
                    max_date_allowed=df['data'].max(),
                    start_date=df['data'].min(),
                    end_date=df['data'].max()
                )
            ], style={'width': '40%', 'display': 'inline-block'})
        ], style={'marginBottom': '30px'}),
        
        # Gráficos principais
        dcc.Tabs([
            dcc.Tab(label='Visão Geral', children=[
                html.Div([
                    dcc.Graph(id='casos-temporais'),
                    dcc.Graph(id='previsoes-grafico')
                ])
            ]),
            
            dcc.Tab(label='Análise de Risco', children=[
                html.Div([
                    dcc.Graph(id='mapa-calor'),
                    dcc.Graph(id='correlacao-clima')
                ])
            ]),
            
            dcc.Tab(label='Alertas', children=[
                html.Div(id='alertas-container', style={'padding': '20px'})
            ])
        ]),
        
        # Armazenamento interno
        dcc.Store(id='filtered-data')
    ])
    
    # Callback para filtrar dados
    @app.callback(
        Output('filtered-data', 'data'),
        Input('municipio-dropdown', 'value'),
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date')
    )
    def filter_data(municipio, start_date, end_date):
        filtered_df = df[df['municipio'] == municipio]
        filtered_df = filtered_df[(filtered_df['data'] >= start_date) & 
                                 (filtered_df['data'] <= end_date)]
        return filtered_df.to_json(date_format='iso', orient='split')
    
    # Callback para gráfico de casos temporais
    @app.callback(
        Output('casos-temporais', 'figure'),
        Input('filtered-data', 'data')
    )
    def update_casos_grafico(data):
        if data is None:
            return go.Figure()
        
        df_filtered = pd.read_json(data, orient='split')
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adicionar casos
        for doenca in ['dengue', 'zika', 'chikungunya']:
            fig.add_trace(
                go.Scatter(
                    x=df_filtered['data'], 
                    y=df_filtered[f'casos_{doenca}'],
                    name=f'Casos de {doenca.capitalize()}',
                    mode='lines+markers'
                ),
                secondary_y=False
            )
        
        # Adicionar variáveis climáticas
        for var in ['temperatura', 'umidade', 'precipitacao']:
            fig.add_trace(
                go.Scatter(
                    x=df_filtered['data'], 
                    y=df_filtered[var],
                    name=var.capitalize(),
                    mode='lines',
                    visible='legendonly'
                ),
                secondary_y=True
            )
        
        fig.update_layout(
            title='Casos de Arboviroses e Variáveis Climáticas',
            xaxis_title='Data',
            legend_title='Variáveis',
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="Casos", secondary_y=False)
        fig.update_yaxes(title_text="Variáveis Climáticas", secondary_y=True)
        
        return fig
    
    # Callback para gráfico de previsões
    @app.callback(
        Output('previsoes-grafico', 'figure'),
        Input('filtered-data', 'data'),
        Input('municipio-dropdown', 'value')
    )
    def update_previsoes_grafico(data, municipio):
        if data is None:
            return go.Figure()
        
        df_filtered = pd.read_json(data, orient='split')
        preds_filtered = predictions[predictions['municipio'] == municipio]
        
        fig = go.Figure()
        
        # Casos reais
        fig.add_trace(go.Scatter(
            x=df_filtered['data'], 
            y=df_filtered['casos_dengue'],
            name='Casos Reais de Dengue',
            mode='lines+markers',
            line=dict(color='blue')
        ))
        
        # Previsões
        fig.add_trace(go.Scatter(
            x=preds_filtered['data'], 
            y=preds_filtered['prob_dengue'] * 100,
            name='Risco de Dengue (%)',
            mode='lines+markers',
            line=dict(color='red', dash='dash'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Casos Reais vs. Previsões de Dengue',
            xaxis_title='Data',
            yaxis_title='Casos',
            yaxis2=dict(
                title='Risco (%)',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        return fig
    
    # Callback para mapa de calor
    @app.callback(
        Output('mapa-calor', 'figure'),
        Input('filtered-data', 'data')
    )
    def update_mapa_calor(data):
        if data is None:
            return go.Figure()
        
        df_filtered = pd.read_json(data, orient='split')
        
        # Agrupar por semana epidemiológica
        heatmap_data = df_filtered.groupby(['semana_epidemiologica', 'ano'])[
            ['casos_dengue', 'casos_zika', 'casos_chikungunya']
        ].sum().reset_index()
        
        fig = px.density_heatmap(
            heatmap_data, 
            x='semana_epidemiologica', 
            y='ano',
            z='casos_dengue',
            title='Distribuição de Casos de Dengue por Semana Epidemiológica e Ano',
            labels={'semana_epidemiologica': 'Semana Epidemiológica', 'ano': 'Ano'},
            histfunc='sum'
        )
        
        return fig
    
    # Callback para correlação com clima
    @app.callback(
        Output('correlacao-clima', 'figure'),
        Input('filtered-data', 'data')
    )
    def update_correlacao_clima(data):
        if data is None:
            return go.Figure()
        
        df_filtered = pd.read_json(data, orient='split')
        
        # Calcular matriz de correlação
        corr_matrix = df_filtered[
            ['temperatura', 'umidade', 'precipitacao', 
             'casos_dengue', 'casos_zika', 'casos_chikungunya']
        ].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1,
            zmax=1
        ))
        
        fig.update_layout(
            title='Correlação entre Variáveis Climáticas e Casos de Arboviroses',
            xaxis_title='Variáveis',
            yaxis_title='Variáveis'
        )
        
        return fig
    
    # Callback para alertas
    @app.callback(
        Output('alertas-container', 'children'),
        Input('municipio-dropdown', 'value')
    )
    def update_alertas(municipio):
        if alerts.empty:
            return html.P("Nenhum alerta recente.")
        
        alertas_filtrados = alerts[alerts['municipio'] == municipio].sort_values('data', ascending=False).head(5)
        
        if alertas_filtrados.empty:
            return html.P("Nenhum alerta recente para este município.")
        
        cards = []
        for _, alerta in alertas_filtrados.iterrows():
            # Determinar cor do card baseado no nível de risco
            risco = alerta['risk_level']
            if risco > 0.8:
                cor = 'danger'
                icone = 'exclamation-triangle'
            elif risco > 0.6:
                cor = 'warning'
                icone = 'exclamation-circle'
            else:
                cor = 'info'
                icone = 'info-circle'
            
            cards.append(html.Div(
                className=f'alert alert-{cor}',
                style={
                    'padding': '15px',
                    'marginBottom': '10px',
                    'borderRadius': '5px'
                },
                children=[
                    html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
                        html.I(className=f"fas fa-{icone} me-2"),
                        html.H4(f"{alerta['doenca']} - {alerta['data'].strftime('%d/%m/%Y')}", 
                                style={'margin': '0', 'flexGrow': '1'}),
                        html.Span(f"Risco: {risco*100:.1f}%", 
                                 style={'fontWeight': 'bold', 'fontSize': '1.2em'})
                    ]),
                    html.P(f"Município: {alerta['municipio']}"),
                    html.P(f"Recomendação: {gerar_recomendacao(alerta['doenca'], risco)}")
                ]
            ))
        
        return html.Div([
            html.H3("Alertas Recentes"),
            html.Div(cards)
        ])
    
    return app

def gerar_recomendacao(doenca, risco):
    """Gera recomendações baseadas no tipo de doença e nível de risco"""
    recomendacoes = {
        'dengue': [
            "Intensificar ações de combate ao mosquito Aedes aegypti",
            "Realizar campanhas de conscientização da população",
            "Aumentar capacidade de atendimento nas unidades de saúde"
        ],
        'zika': [
            "Alertar gestantes sobre os riscos",
            "Reforçar controle vetorial em áreas críticas",
            "Monitorar casos de microcefalia"
        ],
        'chikungunya': [
            "Preparar unidades de saúde para atendimento de dores articulares",
            "Orientar população sobre cuidados com água parada",
            "Implementar medidas de controle vetorial"
        ]
    }
    
    base = recomendacoes.get(doenca.lower(), [])
    if risco > 0.8:
        return base + ["ATIVAR PLANO DE CONTINGÊNCIA", "MOBILIZAR EQUIPES DE EMERGÊNCIA"]
    elif risco > 0.6:
        return base + ["Aumentar vigilância epidemiológica", "Realizar ações preventivas"]
    else:
        return base