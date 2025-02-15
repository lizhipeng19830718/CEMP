# CEMP
CEMP,基于分类增强的多模态检索增强生成框架在医疗数据处理中的优化研究
一、项目代码结构简介：
1.persistent目录：数据的持久化，聊天历史持久化化到pg数据库中，医疗数据扫描件持久化到minio中
2.documents目录：后端通过FastAPI上传的医疗数据扫描件的中转站，只是临时存放医疗数据扫描件。
3.public目录：前端页面元素
4.rag目录：本项目的核心源码，包含了医疗数据的加载、存储、向量化、检索、召回等功能。
5.utils目录：milvus向量数据库接口
6..env文件：环境变量，包含了deepseek、moonshot、qwen等大模型api key的信息，还有milvus、minio、pg数据库的连接配置信息等。
7.app.py文件：后端通过FastAPI上传医疗数据扫描件的接口
8.ui.py文件：前端chainlit界面
9.requirements.txt:项目依赖包
10.evaluate目录：对项目进行评估。执行该部分代码，首先要运行CEMP和localGPT-vision两个项目，得到两份问题/答案文件。
    --load_answers.py：加载标准答案和待验证答案
    --judge_answers.py：调用llm对答案进行判断
    --calculate_accuracy.py：计算答案准确率

二、项目技术框架介绍：
项目前端采用了chainlit框架，数据预处理模块采用了umi-OCR，数据加载采用了docling，整个框架用llamaindex大语言开发框架进行集成
后端接口采用了FastAPI

三、项目运行：
1.pip install -r requirements.txt
2.建议模块化运行，或在终端执行下面命令uvicorn app:app --host 0.0.0.0 --port 80
备注：默认打开80端口页面是进行医疗数据扫描件的上传界面
另外http://localhost:8000/chainlit是前端聊天窗口，用于提问并生成响应答案的界面

