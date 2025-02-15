import os

from pydantic import BaseModel, Field


class RAGConfig(BaseModel):
    milvus_uri: str = Field(default=os.getenv("MILVUS_URI"), description="Milvus URI")
    embedding_model_dim: int = Field(default=512, description="Embedding model dimension")
    moonshot_api_key: str = Field(default=os.getenv("MOONSHOT_API_KEY"), description="Moonshot API key")
    deepseek_api_key: str = Field(default=os.getenv("DEEPSEEK_API_KEY"), description="DeepSeek API key")
    pg_connection_string: str = Field(default=os.getenv("PG_CONNECTION_STRING"), description="Postgres connection string")
    ocr_download_dir: str = Field(default=os.getenv("OCR_DOWNLOAD_PATH"), description="OCR download directory")
    ocr_base_url: str = Field(default=os.getenv("OCR_BASE_URL"), description="OCR base URL")
    vllm_api_key: str = Field(default=os.getenv("VLLM_API_KEY"), description="VLLM API key")
    vllm_base_url: str = Field(default=os.getenv("VLLM_BASE_URL"), description="VLLM base URL")
    vllm_model_name: str = Field(default=os.getenv("VLLM_MODEL_NAME"), description="VLLM model name")
RagConfig = RAGConfig()
