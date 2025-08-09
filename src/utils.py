import os
from dotenv import load_dotenv
from huggingface_hub import login

def safe_hf_login():
    load_dotenv()
    token = os.getenv('HF_API_TOKEN')
    
    if not token:
        raise ValueError("Token do Hugging Face não encontrado!")
    
    try:
        login(token=token)
        return True
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False