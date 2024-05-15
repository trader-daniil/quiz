import os
from enum import Enum
from dotenv import load_dotenv
from telegram import (Update, ForceReply, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove)
"""
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext, ConversationHandler,
                          RegexHandler, ConversationHandler, filters)
"""
from telegram.ext import (
    Updater,

    CommandHandler,

    ConversationHandler,

    MessageHandler,

    Filters,

)
import redis
import random
from functools import partial

load_dotenv()

FOLDERPATH_WITH_QUESTIONS = './quiz-questions'
CUSTOM_KEYBOARD = [['Новый вопрос', 'Сдаться'], 
                   ['Мой счет']]


class QuizStatus(Enum):
    new_question = 0
    answer = 1


def load_questions(folderpath):
    questions = {}
    for filename in os.listdir(FOLDERPATH_WITH_QUESTIONS)[:2]:
        with open(f'{FOLDERPATH_WITH_QUESTIONS}/{filename}', 'r', encoding='KOI8-R') as file:
            question = ''
            quizes = file.read().split('\n\n')
            for quiz in quizes:
                if quiz.startswith('Вопрос'):
                    question = quiz.split(':\n')[1]
                elif quiz.startswith('Ответ'):
                    answer = quiz.split(':\n')[1]
                    questions[question] = answer
    return questions


def start(update, context):
    """Send a message when the command /start is issued."""
    reply_markup = ReplyKeyboardMarkup(CUSTOM_KEYBOARD)
    update.message.reply_markdown_v2(
        text='Привет, я бот для викторин', 
        reply_markup=reply_markup,
    )
    return QuizStatus.new_question.value


def send_question(update: Update, context, questions, redis_con):
    user = update.message.from_user
    question, answer = random.choice(list(questions.items()))
    update.message.reply_text(question)
    redis_con.set(
        user['id'],
        question,
    )
    return QuizStatus.answer.value

def check_answer(update: Update, context, questions, redis_con):
    user = update.message.from_user
    user_answer = update.message.text.split('.')[0]
    question = redis_con.get(user['id']).decode('utf-8')
    answer = questions[question].rstrip('.')
    if user_answer == answer:
        update.message.reply_text('Правильно\! Поздравляю\! Для '
                                  'следующего вопроса нажми «Новый вопрос»')
        return QuizStatus.new_question.value
    else:
        update.message.reply_text('Неправильно, попробуйте еще раз')

        
def cancel(bot, update):
    user = update.message.from_user
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def give_up(update: Update, context, questions, redis_con):
    user = update.message.from_user
    question = redis_con.get(user['id']).decode('utf-8')
    answer = questions[question].rstrip('.')
    update.message.reply_text(answer)
    question, answer = random.choice(list(questions.items()))
    update.message.reply_text(question)
    redis_con.set(
        user['id'],
        question,
    )
    
    return QuizStatus.answer.value


def main() -> None:
    r = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
    )
    tg_token = os.getenv('TG_BOT_TOKEN')
    questions = load_questions(folderpath=FOLDERPATH_WITH_QUESTIONS)
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QuizStatus.new_question.value : [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    partial(
                        send_question,
                        questions=questions,
                        redis_con=r,
            ))],
            QuizStatus.answer.value: [
                MessageHandler(
                    Filters.regex('^Сдаться$'),
                    partial(
                        give_up,
                        questions=questions,
                        redis_con=r,
                    ),
                ),
                MessageHandler(
                    Filters.text & ~Filters.command,
                    partial(
                        check_answer,
                        questions=questions,
                        redis_con=r,
                    )
                ),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
