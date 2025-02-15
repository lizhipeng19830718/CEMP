from llama_index.core import Settings
from .embedding import embed_model_local_bge_small
from .llms import deepseek_llm
Settings.embed_model = embed_model_local_bge_small()
Settings.llm = deepseek_llm()