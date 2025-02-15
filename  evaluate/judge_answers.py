# judge_answers.py
import openai

# 设置OpenAI API密钥
openai.api_key = 'YOUR_API_KEY'  # 替换为你的OpenAI API密钥


def is_answer_correct(standard_answer, test_answer):
    """
    使用大语言模型判断答案是否正确，并获取判断理由。
    返回值为1（正确）或0（错误）。
    """
    prompt = f"判断以下两个答案是否语义相同，并给出理由：\n标准答案：{standard_answer}\n测试答案：{test_answer}\n如果语义相同，请回答'是'，否则回答'否'。"
    response = openai.Completion.create(
        engine="text-davinci-003",  # 选择合适的模型
        prompt=prompt,
        max_tokens=100,  # 设置最大生成长度
        temperature=0.7  # 设置生成的随机性
    )
    result = response.choices[0].text.strip()

    # 判断是否正确，并返回1或0
    if result.lower().startswith('是'):
        return 1, result  # 正确
    else:
        return 0, result  # 错误