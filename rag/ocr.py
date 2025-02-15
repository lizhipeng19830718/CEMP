import base64
import os
import json
import time
import zipfile

import requests
from .config import RagConfig
base_url = RagConfig.ocr_base_url
download_dir = RagConfig.ocr_download_dir
headers = {"Content-Type": "application/json"}

#from .utils import get_b64_image_from_path
def get_b64_image_from_path(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
def _upload_file(file_path):
    url = "{}/api/doc/upload".format(base_url)
    options_json = json.dumps(
        {
            "doc.extractionMode": "mixed",
        }
    )
    with open(file_path, "rb") as file:
        response = requests.post(url, files={"file": file}, data={"json": options_json})
    response.raise_for_status()
    res_data = json.loads(response.text)
    if res_data["code"] == 101:
        # If code == 101, it indicates that the server did not receive the uploaded file.
        # On some Linux systems, if file_name contains non-ASCII characters, this error might occur.
        # In this case, we can specify a temp_name containing only ASCII characters to construct the upload request.
        file_name = os.path.basename(file_path)
        file_prefix, file_suffix = os.path.splitext(file_name)
        temp_name = "temp" + file_suffix

        with open(file_path, "rb") as file:
            response = requests.post(
                url,
                # use temp_name to construct the upload request
                files={"file": (temp_name, file)},
                data={"json": options_json},
            )
        response.raise_for_status()
        res_data = json.loads(response.text)
    file_id = res_data["data"]
    return file_id
def _process_file(file_id):
    url = "{}/api/doc/result".format(base_url)
    print("===================================================")
    print("===== 2. Poll task status until OCR task ends =====")
    print("== URL:", url)

    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(
        {
            "id": file_id,
            "is_data": True,
            "format": "text",
            "is_unread": True,
        }
    )
    while True:
        time.sleep(1)
        response = requests.post(url, data=data_str, headers=headers)
        response.raise_for_status()
        res_data = json.loads(response.text)
        assert res_data["code"] == 100, "Failed to get task status: {}".format(res_data)

        print(
            "    Progress: {}/{}".format(
                res_data["processed_count"], res_data["pages_count"]
            )
        )
        if res_data["data"]:
            print("{}\n========================".format(res_data["data"]))
        if res_data["is_done"]:
            state = res_data["state"]
            assert state == "success", "Task execution failed: {}".format(
                res_data["message"]
            )
            print("OCR task completed.")
            break

def _generate_target_file(file_id):
    url = "{}/api/doc/download".format(base_url)
    print("======================================================")
    print("===== 3. Generate target file, get download link =====")
    print("== URL:", url)

    # Download file parameters
    download_options = {
        "file_types": [
            "txt",
            "txtPlain",
            "jsonl",
            "csv",
            "pdfLayered",
            "pdfOneLayer",
        ],
        # ↓ `ingore_blank` is a typo. If you are using Umi-OCR version 2.1.4 or earlier, please use this incorrect spelling.
        # ↓ If you are using the latest code-built version of Umi-OCR, please use the corrected spelling `ignore_blank`.
        "ingore_blank": False,  # Do not ignore blank pages
    }
    download_options["id"] = file_id
    data_str = json.dumps(download_options)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    res_data = json.loads(response.text)
    assert res_data["code"] == 100, "Failed to get download URL: {}".format(res_data)

    url = res_data["data"]
    name = res_data["name"]
    return name, url

def _download_file(url, name):
    # Save location for downloaded files
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    download_path = os.path.join(download_dir, name)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    # Download file size
    total_size = int(response.headers.get("content-length", 0))
    downloaded_size = 0
    log_size = 10485760  # Print progress every 10MB

    with open(download_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)
                if downloaded_size >= log_size:
                    log_size = downloaded_size + 10485760
                    progress = (downloaded_size / total_size) * 100
                    print(
                        "    Downloading file: {}MB | Progress: {:.2f}%".format(
                            int(downloaded_size / 1048576), progress
                        )
                    )
    print("Target file downloaded successfully: ", download_path)

def _clean_up(file_id):
    url = "{}/api/doc/clear/{}".format(base_url, file_id)
    print("============================")
    print("===== 5. Clean up task =====")
    print("== URL:", url)

    response = requests.get(url)
    response.raise_for_status()
    res_data = json.loads(response.text)
    assert res_data["code"] == 100, "Task cleanup failed: {}".format(res_data)
    print("Task cleaned up successfully.")

    print("======================\nProcess completed.")

def ocr_file_to_text(file_path):
    file_id = _upload_file(file_path)
    _process_file(file_id)
    name, url = _generate_target_file(file_id)
    _download_file(url, name)
    _clean_up(file_id)
    file_name, file_extension = os.path.splitext(file_path)
    file_name_without_extension = os.path.basename(file_name)
    f_name = file_name_without_extension + file_extension
    # zip_file = f"[OCR]_{file_name_without_extension}.zip"
    with zipfile.ZipFile(f"{download_dir}/{name}", 'r') as zip_ref:
        # [OCR]_testdata.layered.pdf
        temp_name = f'[OCR]_{file_name_without_extension}.layered{file_extension}'
        zip_ref.extract(temp_name, download_dir)

        os.rename(download_dir + '/' +temp_name, download_dir + '/' +f_name)
        return download_dir + '/' + f_name

def ocr_image_to_text(file_path):
    import requests
    import json
    data_base64 = get_b64_image_from_path(file_path)
    url = "http://127.0.0.1:1314/api/ocr"
    data = {
        "base64": data_base64,
        # 可选参数示例
        "options": {
            "data.format": "text",
        }
    }
    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(data)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    res_dict = json.loads(response.text)
    return res_dict.get("data")

if __name__ == "__main__":
    file_path = "../test_data/222.jpg"
    ocr_image_to_text(file_path)