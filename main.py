import os
from dotenv import load_dotenv
from src.data_loader import load_data
from src.preprocessor import preprocess_data
from src.model import load_model, predict
from src.dashboard import create_dashboard
from src.alert_system import generate_alerts

def main():
    # 1. Carregar configurações
    load_dotenv()
    print("✅ Configurações carregadas")
    
    # 2. Obter dados
    df = load_data()
    print(f"📊 Dados carregados: {df.shape[0]} registros")
    
    # 3. Pré-processamento
    processed_df = preprocess_data(df)
    print("🧹 Dados pré-processados")
    
    # 4. Carregar modelo
    model, tokenizer = load_model()
    print("🤖 Modelo carregado: mmcleige/arbovirus_bert_base_LR.1e-5_N.5")
    
    # 5. Fazer previsões
    predictions = predict(processed_df, model, tokenizer)
    print("🔮 Previsões geradas")
    
    # 6. Sistema de alerta
    alerts = generate_alerts(predictions)
    print(f"🚨 Alertas gerados: {len(alerts)}")
    
    # 7. Dashboard
    app = create_dashboard(processed_df, predictions, alerts)
    app.run_server(debug=True, port=8050)
    print("📈 Dashboard iniciado: http://localhost:8050")

if __name__ == "__main__":
    main()