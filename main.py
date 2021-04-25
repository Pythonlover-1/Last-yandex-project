from flask import Flask, request
from flask_ngrok import run_with_ngrok
import logging
import functions
import json


threads = []
par = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'}
app = Flask(__name__)
run_with_ngrok(app)
logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': [
                "1000 долларов",
                "5000 рублей"
            ],
            'mon': False,
            'rubles': -1,
            'place': False,
            'spis': [],
            'to': '',
            'from': '',
            'goodbye': False
        }
        res['response']['text'] = 'Привет! Я организую Вам путешествие. Мне нужно только узнать Ваш бюджет и ' \
                                  'город, в который Вы хотите поехать.\nКаков бюджет Вашего путешествия?'
        res['response']['buttons'] = get_suggests()
        return
    if not sessionStorage[user_id]['mon']:
        text = req['request']['command'].lower().split()
        if not (len(text) in (2, 3)):
            res['response']['text'] = 'Данные некорректны!\nПопробуйте ввести бюджет ещё раз'
            res['response']['buttons'] = get_suggests()
            return
        try:
            rubl = float(text[0])
        except ValueError:
            res['response']['text'] = 'Навыку не удаётся определить Ваш бюджет\nПопробуйте ещё раз'
            res['response']['buttons'] = get_suggests()
            return
        try:
            if 'рубл' in ''.join(text) and not ('белорус' in ''.join(text)):
                raise FileNotFoundError
            conv = functions.return_in_rub('+'.join(text))
            rubl = conv[0].text
        except IndexError:
            res['response']['text'] = 'Введённая Вами валюта не опрделена\nПопробуйте ввести бюджет ещё раз'
            res['response']['buttons'] = get_suggests()
            return
        except FileNotFoundError:
            pass
        res['response']['text'] = f'Теперь назовите город, в который хотите поехать'
        sessionStorage[user_id]['mon'] = True
        if isinstance(rubl, str):
            rubl = '.'.join(''.join(rubl.split()).split(','))
        sessionStorage[user_id]['rubles'] = float(rubl)
        res['response']['buttons'] = get_suggests(place=True)
    elif not sessionStorage[user_id]['place']:
        text = req['request']['command'].lower().split()
        city = functions.valid(text)
        if city is None:
            res['response']['text'] = 'Город не определён\nПопробуйте ввести название города ещё раз'
            res['response']['buttons'] = get_suggests(place=True)
            return
        sessionStorage[user_id]['spis'] = functions.return_hotel(city)
        if len(sessionStorage[user_id]['spis']) == 0:
            res['response']['text'] = 'Не найдено гостниц в этом городе\nУкажите более населённый город'
            res['response']['buttons'] = get_suggests(place=True)
            return
        sessionStorage[user_id]['place'] = True
        sessionStorage[user_id]['to'] = city
        res['response']['text'] = 'Топ-5 гостиниц в этом городе:\n\n' + '\n\n\n'.join(sessionStorage[user_id]['spis']) +\
                                  '\n\nТеперь назовите город, из которого Вы хотите отправиться'
        res['response']['tts'] = 'Топ 5 гостиниц в этом городе sil <[2000]>' \
                                 ' Теперь назовите город, из которого Вы хотите отправиться'
        res['response']['buttons'] = get_suggests(place=True)
    elif not sessionStorage[user_id]['goodbye']:
        text = req['request']['command'].lower().split()
        city = functions.valid(text)
        if city is None:
            res['response']['text'] = 'Город не определён\nПопробуйте ввести название города ещё раз'
            res['response']['buttons'] = get_suggests(place=True)
            return
        if city == sessionStorage[user_id]['to']:
            res['response']['text'] = 'Некорректный ввод\nВведите, пожалуйста, другой город'
            res['response']['buttons'] = get_suggests(place=True)
            return
        sessionStorage[user_id]['from'] = city
        c1 = sessionStorage[user_id]['to']
        c2 = sessionStorage[user_id]['from']
        marsh = functions.rasp(c1.split(', ')[-1], c2.split(', ')[-1])
        if len(marsh) == 0:
            res['response']['text'] = 'Системам Яндекс не удаётся построить маршрут\nПришло время прощаться.' \
                                                                    '\nДля завершения работы навыка скажите что угодно'
            res['response']['buttons'] = get_suggests(place=True)
            sessionStorage[user_id]['goodbye'] = True
            return
        res['response']['tts'] = 'Возможные маршруты sil <[2000]> пришло время прощаться. ' \
                                 'Для завершения работы навыка скажите что угодно'
        res['response']['text'] = 'Возможные маршруты:\n' + marsh + '\nПришло время прощаться.' \
                                                                    '\nДля завершения работы навыка скажите что угодно'
        sessionStorage[user_id]['goodbye'] = True
    else:
        if sessionStorage[user_id]['rubles'] <= 10000:
            res['response']['text'] = 'На Ваш бюджет Вы можете покушать мороженое или сходить в парк'
            res['response']['tts'] = 'На Ваш бюджет Вы можете пок+ушать мороженое или сходить в парк'
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'На Ваш бюджет Вы можете покушать мороженое или сходить в парк'
            res['response']['card']['image_id'] = '1521359/51474724e06f18912714'
        elif sessionStorage[user_id]['rubles'] <= 40000:
            res['response']['text'] = 'На Ваш бюджет Вы можете пойти в парк аттракционов'
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'На Ваш бюджет Вы можете пойти в парк аттракционов'
            res['response']['card']['image_id'] = '213044/2837ec2353aa7451f304'
        else:
            res['response']['text'] = 'На Ваш бюджет Вы можете позволить себе всё, что угодно'
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'На Ваш бюджет Вы можете позволить себе всё, что угодно'
            res['response']['card']['image_id'] = '965417/313691e747ed4ec1d494'
        res['response']['end_session'] = True


def get_suggests(place=False):
    if not place:
        return [{'title': '1000 долларов', 'hide': True}, {'title': '5000 рублей', 'hide': True}]
    return [{'title': 'Прага', 'hide': True}, {'title': 'Мюнхен', 'hide': True}]


if __name__ == '__main__':
    app.run()