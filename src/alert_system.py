import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

def generate_alerts(predictions, threshold=0.7):
    """
    Gera alertas quando o risco excede um limiar
    
    Args:
        predictions: DataFrame com previsões do modelo
        threshold: Limiar de risco (0-1)
        
    Returns:
        DataFrame com alertas
    """
    alerts = []
    
    # Verificar cada linha de previsão
    for _, row in predictions.iterrows():
        # Determinar qual doença tem o maior risco
        riscos = {
            'dengue': row['prob_dengue'],
            'zika': row['prob_zika'],
            'chikungunya': row['prob_chikungunya']
        }
        
        doenca_max = max(riscos, key=riscos.get)
        risco_max = riscos[doenca_max]
        
        if risco_max >= threshold:
            alerts.append({
                'data': row['data'],
                'municipio': row['municipio'],
                'doenca': doenca_max.capitalize(),
                'risk_level': risco_max
            })
    
    # Converter para DataFrame
    alerts_df = pd.DataFrame(alerts)
    
    # Enviar alertas por email se houver novos
    if not alerts_df.empty:
        send_email_alerts(alerts_df)
    
    return alerts_df

def send_email_alerts(alerts_df):
    """Envia alertas por email"""
    load_dotenv()
    email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    email_port = int(os.getenv('EMAIL_PORT', 587))
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    recipient = os.getenv('ALERT_RECIPIENT', email_user)
    
    if not email_user or not email_password:
        print("Credenciais de email não configuradas. Alertas não enviados.")
        return
    
    # Criar mensagem
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = recipient
    msg['Subject'] = f"ALERTA: {len(alerts_df)} novos alertas de arboviroses"
    
    # Criar corpo do email
    body = "<h2>Alertas de Arboviroses</h2>"
    body += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>Data</th><th>Município</th><th>Doença</th><th>Risco</th></tr>"
    
    for _, alerta in alerts_df.iterrows():
        body += f"<tr><td>{alerta['data'].strftime('%d/%m/%Y')}</td><td>{alerta['municipio']}</td><td>{alerta['doenca']}</td><td>{alerta['risk_level']*100:.1f}%</td></tr>"
    
    body += "</table>"
    body += "<p><strong>Ações recomendadas:</strong> Verificar sistema de vigilância e intensificar medidas de controle vetorial.</p>"
    
    msg.attach(MIMEText(body, 'html'))
    
    # Enviar email
    try:
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()
        server.login(email_user, email_password)
        server.sendmail(email_user, recipient, msg.as_string())
        server.quit()
        print(f"📧 Alertas enviados por email para {recipient}")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")