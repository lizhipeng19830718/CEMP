# pip install llama-index-embeddings-huggingface
# pip install llama-index-embeddings-instructor

# pip install llama-index-embeddings-ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 本地模型
def embed_model_local_bge_small(**kwargs):
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5",
                                       cache_folder=r"D:\ai_project\embed_cache",
                                       **kwargs)
    return embed_model
# 在线模型
