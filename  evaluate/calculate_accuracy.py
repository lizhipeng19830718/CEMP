# calculate_accuracy.py
from judge_answers import is_answer_correct

def calculate_accuracy(standard_answers, test_answers):
    """
    计算测试答案的正确率，并记录每个问题的判断理由。
    """
    correct_count = 0
    total_count = len(standard_answers)
    reasons = []

    for question, standard_answer in standard_answers.items():
        if question in test_answers:
            test_answer = test_answers[question]
            score, reason = is_answer_correct(standard_answer, test_answer)
            reasons.append(f"问题: {question}\n标准答案: {standard_answer}\n测试答案: {test_answer}\n评分: {score}\n理由: {reason}\n")
            correct_count += score

    accuracy = correct_count / total_count if total_count > 0 else 0
    return accuracy, reasons