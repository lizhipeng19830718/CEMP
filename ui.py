import os
import random
from typing import Optional, List

import chainlit as cl
from chainlit.element import ElementBased
from chainlit.input_widget import Select, Switch
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage

from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.memory import ChatMemoryBuffer

from rag.traditional_rag import TraditionalRAG
from rag.multimodal_rag import MultiModalRAG
from persistent.minio_storage_client import MinioStorageClient
from persistent.postgresql_data_layer import PostgreSQLDataLayer
import chainlit.data as cl_data
from rag.config import RagConfig
from utils.milvus import list_collections
from rag.base_rag import RAG
load_dotenv()
# 实现聊天数据持久化
storage_client = MinioStorageClient()
cl_data._data_layer = PostgreSQLDataLayer(conninfo=RagConfig.pg_connection_string, storage_provider=storage_client)


async def view_pdf(elements: List[ElementBased]):
    """查看PDF文件"""
    files = []
    contents = []
    for element in elements:
        if element.name.endswith(".pdf"):
            pdf = cl.Pdf(name=element.name, display="side", path=element.path)
            files.append(pdf)
            contents.append(element.name)
    if len(files) == 0:
        return
    await cl.Message(content=f"查看PDF文件：" + "，".join(contents), elements=files).send()

@cl.set_chat_profiles
async def chat_profile(current_user: cl.User):
    if current_user.metadata["role"] != "admin":
        return None
    # 知识库信息最后存储在关系数据库中:名称，描述，图标
    kb_list = list_collections()
    profiles = [
        cl.ChatProfile(
            name="default",
            markdown_description=f"大模型对话",
            icon=f"/public/kbs/4.png",
        )
    ]
    for kb_name in kb_list:
        profiles.append(
            cl.ChatProfile(
                name=kb_name,
                markdown_description=f"{kb_name} 知识库",
                icon=f"/public/kbs/{random.randint(1, 3)}.jpg",
            )
        )
    return profiles

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="大模型提高软件测试效率",
            message="详细介绍如何借助大语言模型提高软件测试效率。",
            icon="/public/apidog.svg",
            ),
        cl.Starter(
            label="自动化测试思路",
            message="详细描述一下接口及UI自动化测试的基本思路。",
            icon="/public/pulumi.svg",
            ),
        cl.Starter(
            label="性能测试分析及瓶颈定位思路",
            message="详细描述一下软件性能测试分析及瓶颈定位的核心思路。",
            icon="/public/godot_engine.svg",
            ),
        cl.Starter(
            label="如何学习大模型应用的核心技术",
            message="给出学习大语言模型的一些重要的技术和方法。",
            icon="/public/gleam.svg",
            )
        ]


@cl.on_chat_start
async def start():
    await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="模型选择",
                values=["DeepSeek", "Moonshot", ],
                initial_index=0,
            ),
            Switch(id="multimodal", label="多模态RAG", initial=True),
        ]
    ).send()

    kb_name = cl.user_session.get("chat_profile")
    # 选择默认知识库，是与大模型直接对话
    if kb_name is None or kb_name == "default":
        memory = ChatMemoryBuffer.from_defaults(token_limit=1024)
        chat_engine = SimpleChatEngine.from_defaults(memory=memory)
    else:
        index = await RAG.load_index(collection_name=kb_name)
        chat_engine = index.as_chat_engine(chat_mode=ChatMode.CONTEXT)

    cl.user_session.set("chat_engine", chat_engine)


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    # 可以对接第三方认证
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin",
                       metadata={"role": "admin", "provider": "credentials"})
    else:
        return None

@cl.on_settings_update
async def setup_settings(settings):
    cl.user_session.set("settings", settings)

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    chat_engine = SimpleChatEngine.from_defaults()
    for message in thread.get("steps", []):
        if message["type"] == "user_message":
            chat_engine.chat_history.append(ChatMessage(content=message["output"], role="user"))
        elif message["type"] == "assistant_message":
            chat_engine.chat_history.append(ChatMessage(content=message["output"], role="assistant"))

    cl.user_session.set("chat_engine", chat_engine)

@cl.on_message
async def main(message: cl.Message):
    chat_engine = cl.user_session.get("chat_engine")
    msg = cl.Message(content="", author="Assistant")
    # 预览pdf
    await view_pdf(message.elements)

    files = []
    # 获取用户上传的文件（包含图片）
    for element in message.elements:
        if isinstance(element, cl.File) or isinstance(element, cl.Image):
            files.append(element.path)
    # 文件索引处理
    if len(files) > 0:
        # 获取设置页面上的所有参数
        m = cl.user_session.get("settings")
        # 开启多模态对话
        if m is None or m.get("multimodal"):
            rag = MultiModalRAG(files=files)
        else:
            rag = TraditionalRAG(files=files)

        index = await rag.create_index_local()
        chat_engine = index.as_chat_engine(chat_mode=ChatMode.CONTEXT)
        cl.user_session.set("chat_engine", chat_engine)

    res = await cl.make_async(chat_engine.stream_chat)(message.content)

    # 流式界面输出
    for token in res.response_gen:
        await msg.stream_token(token)

    # 显示图片
    for source_node in res.source_nodes:
        if source_node.metadata["type"] == "image":
            msg.elements.append(
                cl.Image(path=source_node.metadata["image"],
                         name=source_node.metadata["source"],
                         display="inline"))

    # 显示数据来源
    if not isinstance(chat_engine, SimpleChatEngine):
        source_names = []
        for idx, node_with_score in enumerate(res.source_nodes):
            node = node_with_score.node
            source_name = f"source_{idx}"
            source_names.append(source_name)
            msg.elements.append(
                cl.Text(content=node.get_text(),
                        name=source_name,
                        display="side")
            )
        await msg.stream_token(f"\n\n **数据来源**: {', '.join(source_names)}")
    await msg.send()
