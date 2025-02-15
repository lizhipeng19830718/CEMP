import os.path

from chainlit.utils import mount_chainlit
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse

from rag.multimodal_rag import MultiModalRAG
from rag.traditional_rag import TraditionalRAG
from utils.r import R
app = FastAPI()

@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile], collection_name: str = Form(), multimodal: bool = Form()):
    file_list = []
    for file in files:
        file_path = os.path.join("documents", os.path.basename(file.filename))
        with open(file_path, "wb+") as f:
            f.write(await file.read())
            file_list.append(file_path)
    if multimodal:
        rag = MultiModalRAG(files=file_list)
    else:
        rag = TraditionalRAG(files=file_list)
    await rag.create_index(collection_name=collection_name)
    return R.ok("index success")


# @app.get("/")
# async def main():
#     content = """
#         <body>
#         <form action="/files/" enctype="multipart/form-data" method="post">
#         <input name="files" type="file" multiple>
#         <input type="submit">
#         </form>
#         <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
#         <input name="files" type="file" multiple>
#         <input type="submit">
#         </form>
#         </body>
#     """
#     return HTMLResponse(content=content)

mount_chainlit(app=app, target="ui.py", path="/chainlit")
# 启动fastapi命令： uvicorn main:app --host 0.0.0.0 --port 80