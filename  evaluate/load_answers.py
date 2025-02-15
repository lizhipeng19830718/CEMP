# load_answers.py

def load_answers(file_path):
    """
    加载文件中的问答对，返回一个字典，键是问题，值是答案。
    """
    answers = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('|')  # 假设问题和答案之间用'|'分隔
                if len(parts) == 2:
                    question, answer = parts
                    answers[question.strip()] = answer.strip()
    return answers