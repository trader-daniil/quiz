import random

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
import os
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from functools import partial
import redis
import random
from quiz_questions import load_questions

FOLDERPATH_WITH_QUESTIONS = './quiz-questions'
load_dotenv()



def give_up(event, vk_api, keyboard, questions, redis_con):
    print('Сдаетесь')
    question = redis_con.get(event.user_id).decode('utf-8')
    answer = questions[question].rstrip('.')
    vk_api.messages.send(
        user_id=event.user_id,
        message=answer,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )
    question, answer = random.choice(list(questions.items()))
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )
    redis_con.set(
        event.user_id,
        question,
    )


def send_question(event, vk_api, keyboard, questions, redis_con):
    question, answer = random.choice(list(questions.items()))
    redis_con.set(
        event.user_id,
        question,
    )
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


def check_answer(event, vk_api, keyboard, questions, redis_con):
    user_answer = event.text.split('.')[0]
    question = redis_con.get(event.user_id).decode('utf-8')
    answer = questions[question].rstrip('.')
    if user_answer == answer:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Правильно\! Поздравляю\! Для '
                    'следующего вопроса нажми «Новый вопрос»',
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1,1000)
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Неправильно, попробуйте еще раз',
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1,1000)
        )


if __name__ == "__main__":
    r = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
    )
    questions = load_questions(folderpath=FOLDERPATH_WITH_QUESTIONS)
    vk_token = os.getenv('VK_TOKEN')
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                send_question(
                    event=event,
                    vk_api=vk_api,
                    keyboard=keyboard,
                    questions=questions,
                    redis_con=r,
                )
            elif event.text == 'Сдаться':
                give_up(
                    event=event,
                    vk_api=vk_api,
                    keyboard=keyboard,
                    questions=questions,
                    redis_con=r,
                )
            else:
                check_answer(
                    event=event,
                    vk_api=vk_api,
                    keyboard=keyboard,
                    questions=questions,
                    redis_con=r,
                )
