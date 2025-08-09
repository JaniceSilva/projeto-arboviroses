from transformers import AutoModel, AutoTokenizer
from .utils import safe_hf_login

def load_arbovirus_model():
    if not safe_hf_login():
        return None, None
    
    try:
        model = AutoModel.from_pretrained("mmcleige/arbovirus_bert_base_LR.1e-5_N.5")
        tokenizer = AutoTokenizer.from_pretrained("mmcleige/arbovirus_bert_base_LR.1e-5_N.5")
        return model, tokenizer
    except Exception as e:
        print(f"Erro ao carregar modelo: {e}")
        return None, None