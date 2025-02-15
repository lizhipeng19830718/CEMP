# main.py
from load_answers import load_answers
from calculate_accuracy import calculate_accuracy

# 加载标准答案和测试答案
standard_answers = load_answers('A.txt')  # A文件路径
answers_b = load_answers('B.txt')         # B文件路径
answers_c = load_answers('C.txt')         # C文件路径

# 计算正确率并获取判断理由
accuracy_b, reasons_b = calculate_accuracy(standard_answers, answers_b)
accuracy_c, reasons_c = calculate_accuracy(standard_answers, answers_c)

print(f"B文件的正确率: {accuracy_b:.2%}")
print(f"C文件的正确率: {accuracy_c:.2%}")

# 打印判断理由
print("\nB文件的判断理由：")
for reason in reasons_b:
    print(reason)

print("\nC文件的判断理由：")
for reason in reasons_c:
    print(reason)