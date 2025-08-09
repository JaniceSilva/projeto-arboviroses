from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import pandas as pd
import os

def load_model():
    model_name = "mmcleige/arbovirus_bert_base_LR.5e-5_N.5"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        return model, tokenizer
    except Exception as e:
        print(f"🔥 Erro ao carregar modelo: {e}")
        return None, None

def predict(df, model, tokenizer):
    if model is None or tokenizer is None:
        return pd.DataFrame()
    
    results = []
    
    for _, row in df.iterrows():
        # Criar texto para classificação
        text = (
            f"Relatório de {row['municipio']} em {row['data']}: "
            f"Temp: {row['temperatura']}°C, Umidade: {row['umidade']}%, "
            f"Precipitação: {row['precipitacao']}mm. "
            f"Casos: D{row['casos_dengue']} Z{row['casos_zika']} C{row['casos_chikungunya']}"
        )
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        results.append({
            'data': row['data'],
            'municipio': row['municipio'],
            'prob_dengue': probs[0][0].item(),
            'prob_zika': probs[0][1].item(),
            'prob_chikungunya': probs[0][2].item(),
            'risk_level': max(probs[0]).item()
        })
    
    return pd.DataFrame(results)