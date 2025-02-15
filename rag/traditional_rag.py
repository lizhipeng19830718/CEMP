import asyncio
import os
from datetime import datetime

from llama_index.core import SimpleDirectoryReader, Document

from .base_rag import RAG
from .utils import ocr_file_to_text_llm, is_image
from .ocr import ocr_file_to_text, ocr_image_to_text

class TraditionalRAG(RAG):
    async def load_data(self):
        docs = []
        for file in self.files:
            # 对图片及文档通过Moonshot大模型进行OCR识别
            # contents = ocr_file_to_text_llm(file)
            # 判断文件类型
            if is_image(file):
                contents = ocr_image_to_text(file)
                temp_file = datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(contents)
                    f_name = temp_file
            else:
                f_name = ocr_file_to_text(file)
            # temp_file = datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
            # with open(temp_file, "w", encoding="utf-8") as f:
            #     f.write(contents)

            data = SimpleDirectoryReader(input_files=[f_name]).load_data()
            doc = Document(text="\n\n".join([d.text for d in data[0:]]), metadata={"path": file})
            docs.append(doc)
            os.remove(f_name)
        return docs

 # if __name__ == "__main__":
 #     rag = TraditionalRAG(files=["../test_data/222.jpg"])
 #     asyncio.run(rag.create_index_local())



