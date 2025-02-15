import os
import fitz
from llama_index.core import Document
from llama_index.core.async_utils import run_jobs

from .base_rag import RAG
from .utils import (describe_image, process_text_blocks,
                   extract_text_around_item, process_table,
                   convert_ppt_to_pdf, convert_pdf_to_images, extract_text_and_notes_from_ppt, save_uploaded_file)
class MultiModalRAG(RAG):
    @staticmethod
    def parse_all_tables(filename, page, pagenum, text_blocks, ongoing_tables):
        """
        从PDF页面中提取表格并处理成文档。
        该函数在给定的PDF页面上识别表格，将表格转换为pandas DataFrame，并将其保存为Excel文件，
        捕获表格的图像，并收集周围的文本以提供上下文。它为每个表格构建一个文档对象，包括源文件名、
        页码和表格图像等元数据。函数在表格提取过程中处理异常，防止因单个错误导致整个过程失败。

        参数:
        - filename: 被处理的PDF文件的名称。
        - page: 当前处理的页面对象。
        - pagenum: 页面编号。
        - text_blocks: 页面上的文本块列表。
        - ongoing_tables: 正在处理的表格列表。

        返回值:
        - table_docs: 包含所有表格文档的列表。
        - table_bboxes: 包含所有表格边界框的列表。
        - ongoing_tables: 更新后的正在处理的表格列表。
        """
        table_docs = []
        table_bboxes = []
        try:
            # 在页面上查找表格
            tables = page.find_tables(horizontal_strategy="lines_strict", vertical_strategy="lines_strict")

            for tab in tables:
                if not tab.header.external:
                    # 将表格转换为pandas DataFrame
                    pandas_df = tab.to_pandas()

                    # 创建存储表格引用的目录
                    tablerefdir = os.path.join(os.getcwd(), "vectorstore/table_references")
                    os.makedirs(tablerefdir, exist_ok=True)

                    # 保存表格为Excel文件
                    df_xlsx_path = os.path.join(tablerefdir, f"table{len(table_docs)+1}-page{pagenum}.xlsx")
                    pandas_df.to_excel(df_xlsx_path)

                    # 获取表格的边界框
                    bbox = fitz.Rect(tab.bbox)
                    table_bboxes.append(bbox)

                    # 提取表格周围的文本
                    before_text, after_text = extract_text_around_item(text_blocks, bbox, page.rect.height)

                    # 获取表格的图像并保存
                    table_img = page.get_pixmap(clip=bbox)
                    table_img_path = os.path.join(tablerefdir, f"table{len(table_docs)+1}-page{pagenum}.jpg")
                    table_img.save(table_img_path)
                    # 获取表格内容及描述
                    content, description = process_table(table_img_path)
                    # 构建表格的标题
                    caption = before_text.replace("\n", " ") + " ".join(tab.header.names) + after_text.replace("\n", " ")

                    # 构建表格的元数据
                    table_metadata = {
                        "source": f"{filename[:-4]}-page{pagenum}-table{len(table_docs)+1}",
                        "dataframe": df_xlsx_path,
                        "image": table_img_path,
                        "caption": caption,
                        "type": "table",
                        "page_num": pagenum
                    }
                    # 获取所有列名
                    all_cols = ", ".join(list(pandas_df.columns.values))

                    # 构建文档对象
                    doc = Document(text=f"这是一个表格，标题是: {caption}\n表格的内容是：{content}\n表格的列名是： {all_cols}\n表格的解释是：{description}", metadata=table_metadata)
                    table_docs.append(doc)
        except Exception as e:
            # 处理表格提取过程中出现的异常
            print(f"Error during table extraction: {e}")

        return table_docs, table_bboxes, ongoing_tables

    @staticmethod
    def parse_all_images(filename, page, pagenum, text_blocks):
        """
        从PDF页面中提取所有图像，并生成包含图像及其元数据的文档列表。

        参数:
        - filename (str): PDF文件名。
        - page (fitz.Page): 当前处理的PDF页面对象。
        - pagenum (int): 页面编号。
        - text_blocks (list): 页面上的文本块列表。
        返回:
        - image_docs (list): 包含提取的图像及其元数据的文档列表。
        """

        image_docs = []  # 初始化存储图像文档的列表
        image_info_list = page.get_image_info(xrefs=True)  # 获取页面中所有图像的信息
        page_rect = page.rect  # 获取页面的矩形区域

        # 遍历页面中的所有图像信息
        for image_info in image_info_list:
            xref = image_info['xref']  # 获取图像的XREF编号
            if xref == 0:
                continue  # 跳过无效的XREF编号

            img_bbox = fitz.Rect(image_info['bbox'])  # 获取图像的边界框
            # 过滤掉尺寸过小的图像
            if img_bbox.width < page_rect.width / 20 or img_bbox.height < page_rect.height / 20:
                continue

            extracted_image = page.parent.extract_image(xref)  # 提取图像数据
            image_data = extracted_image["image"]  # 获取图像的二进制数据
            imgrefpath = os.path.join(os.getcwd(), "vectorstore/image_references")  # 图像保存路径
            os.makedirs(imgrefpath, exist_ok=True)  # 创建保存路径目录
            image_path = os.path.join(imgrefpath, f"image{xref}-page{pagenum}.png")  # 图像文件名

            # 图片上传到minio 文件服务器
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)  # 将图像数据写入文件

            before_text, after_text = extract_text_around_item(text_blocks, img_bbox, page.rect.height)  # 获取图像周围的文本
            # 1、可以借助多模态模型进行图像描述，2、借助orc识别描述，3、尝试多维度描述该图片
            image_description = describe_image(image_path)
            caption = before_text.replace("\n", " ")

            image_metadata = {
                "source": f"{filename[:-4]}-page{pagenum}-image{xref}",  # 图像来源
                "image": image_path,  # 图像路径
                "caption": caption,  # 图像标题
                "type": "image",  # 图像类型
                "page_num": pagenum  # 图像所在页码
            }
            image_docs.append(Document(text="这是一张图像，标题是： " + caption + f"\n图像的描述是：{before_text}\n" + image_description + f"\n{after_text}", metadata=image_metadata))  # 添加图像文档到列表

        return image_docs  # 返回包含图像及其元数据的文档列表

    @staticmethod
    def process_pdf_file(pdf_file):
        """
        处理 PDF 文件并提取文本、表格和图像。
        该函数读取一个 PDF 文件，从每一页中提取所有文本块、表格和图像，并将它们作为 Document 对象列表返回。
        它会避免提取页面的页眉和页脚。

        :param pdf_file: 表示要处理的 PDF 文件的文件对象。
        :return: 包含提取信息的 Document 对象列表。
        """
        # 初始化一个列表来存储所有提取的 Document 对象
        all_pdf_documents = []
        # 初始化一个字典来跟踪跨页的持续表格
        ongoing_tables = {}

        # 尝试打开 PDF 文件
        try:
            f = fitz.open(filename=pdf_file, filetype="pdf")
        except Exception as e:
            print(f"pdf文件打开发生错误: {e}")
            return []

        file_name = os.path.basename(pdf_file)
        # 遍历 PDF 的每一页
        for i in range(len(f)):
            page = f[i]
            # 从页面中提取文本块，排除可能的页眉和页脚
            text_blocks = [block for block in page.get_text("blocks", sort=True)
                           if block[-1] == 0 and not (block[1] < page.rect.height * 0.1 or block[3] > page.rect.height * 0.9)]
            # 组织文本块以更好地分类
            grouped_text_blocks = process_text_blocks(text_blocks)

            # 从页面中解析表格，必要时更新持续表格
            table_docs, table_bboxes, ongoing_tables = MultiModalRAG.parse_all_tables(file_name, page, i, text_blocks, ongoing_tables)
            all_pdf_documents.extend(table_docs)

            # 从页面中解析图像
            image_docs = MultiModalRAG.parse_all_images(file_name, page, i, text_blocks)
            all_pdf_documents.extend(image_docs)

            # 遍历组织后的文本块
            for text_block_ctr, (heading_block, content) in enumerate(grouped_text_blocks, 1):
                heading_bbox = fitz.Rect(heading_block[:4])
                # 检查标题框是否与任何表格框相交
                if not any(heading_bbox.intersects(table_bbox) for table_bbox in table_bboxes):
                    bbox = {"x1": heading_block[0], "y1": heading_block[1], "x2": heading_block[2], "x3": heading_block[3]}
                    # 创建一个 Document 对象来存储文本块
                    text_doc = Document(
                        text=f"{heading_block[4]}\n{content}",
                        metadata={
                            **bbox,
                            "type": "text",
                            "page_num": i,
                            "source": f"{file_name[:-4]}-page{i}-block{text_block_ctr}"
                        },
                        id_=f"{file_name[:-4]}-page{i}-block{text_block_ctr}"
                    )
                    all_pdf_documents.append(text_doc)

        # 关闭 PDF 文件
        f.close()
        return all_pdf_documents

    @staticmethod
    def process_ppt_file(ppt_file):
        """
        处理PowerPoint文件。
        参数:
        - ppt_path (str): PowerPoint文件的路径。

        返回:
        - list: 包含处理后的数据列表，每个元素是一个Document对象。
        """
        # 将PPT文件转换为PDF文件
        pdf_path = convert_ppt_to_pdf(ppt_file)

        # 将PDF文件的每一页转换为图像
        images_data = convert_pdf_to_images(pdf_path)

        # 从PPT文件中提取每张幻灯片的文本和备注
        slide_texts = extract_text_and_notes_from_ppt(ppt_file)

        processed_data = []

        # 遍历每张幻灯片的图像和文本信息
        for (image_path, page_num), (slide_text, notes) in zip(images_data, slide_texts):
            if notes:
                notes = "\n\nThe speaker notes for this slide are: " + notes

            image_description = describe_image(image_path)
            # 构建图像元数据
            image_metadata = {
                "source": f"{os.path.basename(ppt_file)}",
                "image": image_path,
                "caption": slide_text + image_description + notes,
                "type": "image",
                "page_num": page_num
            }

            # 创建Document对象并添加到处理后的数据列表中
            processed_data.append(Document(text="这是一张带文本的幻灯片: " + slide_text + image_description, metadata=image_metadata))

        return processed_data

    async def load_data(self) -> list[Document]:
        """Load and process multiple file types."""
        documents = []
        tasks = []
        for file_path in self.files:
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name.lower())[1]
            if file_extension in ('.png', '.jpg', '.jpeg'):
                async def process_image(image_path):
                    # 借助多模态大模型获取图片的解读
                    # 建议多维度描述该图片，可以尝试多次调用
                    image_text = describe_image(image_path)
                    doc = Document(text=image_text, metadata={"source": file_name, "type": "image", "image": image_path})
                    documents.append(doc)
                task = process_image(file_path)
                tasks.append(task)
            elif file_extension == '.pdf':
                try:
                    async def process_pdf(pdf_path):
                        pdf_documents = MultiModalRAG.process_pdf_file(pdf_path)
                        documents.extend(pdf_documents)
                    task = process_pdf(file_path)
                    tasks.append(task)
                except Exception as e:
                    print(f"Error processing PDF {file_name}: {e}")
            elif file_extension in ('.ppt', '.pptx'):
                try:
                    async def process_ppt(ppt_path):
                        ppt_documents = MultiModalRAG.process_ppt_file(save_uploaded_file(ppt_path))
                        documents.extend(ppt_documents)
                    task = process_ppt(file_path)
                    tasks.append(task)
                except Exception as e:
                    print(f"Error processing PPT {file_name}: {e}")
            else:
                async def process_text():
                    with open(file_path, "rb") as file:
                        text = file.read().decode("utf-8")
                        doc = Document(text=text, metadata={"source": file.name, "type": "text"})
                        documents.append(doc)
                task = process_text()
                tasks.append(task)
        # await asyncio.gather(*tasks)
        await run_jobs(tasks, show_progress=True, workers=3)
        return documents

