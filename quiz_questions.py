import os


def load_questions(folderpath):
    questions = {}
    for filename in os.listdir(folderpath):
        with open(f'{folderpath}/{filename}', 'r', encoding='KOI8-R') as file:
            question = ''
            quizes = file.read().split('\n\n')
            for quiz in quizes:
                if quiz.startswith('Вопрос'):
                    question = quiz.split(':\n')[1]
                elif quiz.startswith('Ответ'):
                    answer = quiz.split(':\n')[1]
                    questions[question] = answer
    return questions