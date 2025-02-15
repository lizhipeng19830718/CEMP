from typing import Dict

from llama_index.llms.openai import OpenAI as DeepSeeK
from openai import OpenAI
from .config import RagConfig
from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, CHAT_MODELS
DEEPSEEK_MODELS: Dict[str, int] = {
    "deepseek-chat": 128000,
}
ALL_AVAILABLE_MODELS.update(DEEPSEEK_MODELS)
CHAT_MODELS.update(DEEPSEEK_MODELS)

def moonshot_llm(**kwargs):
    llm = OpenAI(api_key=RagConfig.moonshot_api_key,
                 base_url="https://api.moonshot.cn/v1",
                 **kwargs)
    return llm


def deepseek_llm(**kwargs):
    llm = DeepSeeK(api_key=RagConfig.deepseek_api_key,
                 model="deepseek-chat",
                 api_base="https://api.deepseek.com/v1",
                 temperature=0.7,
                 **kwargs)
    return llm

def vllm(**kwargs):
    from openai import OpenAI
    llm = OpenAI(api_key=RagConfig.vllm_api_key,
                 base_url=RagConfig.vllm_base_url,
                 **kwargs)
    return llm