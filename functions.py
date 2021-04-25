import requests
import cities
from bs4 import BeautifulSoup


def rasp(city1, city2):
    url = f'https://api.rasp.yandex.net/v3.0/search/?' \
          f'apikey=7244a75c-ea49-464c-b891-1b51c9e94cff&' \
          f'limit=50&transfers=0&format=json&from=c{cities.return_code(city1)}&to=c{cities.return_code(city2)}'
    response = requests.get(url)
    json_read = response.json()['segments']
    spis = []
    for it in json_read:
        if 'ежедневно' in it['days']:
            spis.append(f'Место отправления: {it["from"]["station_type_name"] + " " + it["from"]["title"]}\n'
                        f'Место прибытия: {it["to"]["station_type_name"] + " " + it["to"]["title"]}\n'
                        f'Маршрут доступен {it["days"]}\n')
            block = it['thread']['carrier']
            if len(block['url']) + len(block['phone']) == 0:
                spis[-1] += f'Примечание: {block["contacts"]}\n'
            else:
                if len(block['phone']) != 0:
                    spis[-1] += f'Телефон организации перевозок: {block["phone"]}\n'
                if len(block['url']) != 0:
                    spis[-1] += f'Сайт организации перевозок: {block["url"]}\n'
        if len(spis) == 3:
            break
    return '\n'.join(list(set(spis)))


def valid(text):
    request = f'https://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-' \
              f'98533de7710b&geocode={text}&format=json'
    response = requests.get(request)
    json_read = response.json()['response']
    if int(json_read['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found']) == 0:
        return None
    flag = False
    for e in json_read['GeoObjectCollection']['featureMember']:
        if e['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind'] in ('locality', 'province'):
            flag = True
            break
    if flag:
        name = e['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
        return name
    return None


def return_hotel(city):
    spis = []
    request = f"https://search-maps.yandex.ru/v1/?text=гостиницы в городе {city}&results=5&" \
              f"lang=ru_RU&apikey=63eb0fda-03cc-4a79-9044-b11ac3e60e7e"
    response = requests.get(request)
    json_read = response.json()
    for x in json_read['features']:
        spis.append([x['properties']['name'], x['properties']['CompanyMetaData']['address']])
        try:
            spis[-1].append(x['properties']['CompanyMetaData']['Phones'][0]['formatted'])
        except KeyError:
            pass
        try:
            spis[-1].append(x['properties']['CompanyMetaData']['url'])
        except KeyError:
            pass
    spis = [f'Гостница: {it[0]}\nАдрес: {it[1]}' if len(it) == 2
            else f'Гостница: {it[0]}\nАдрес: {it[1]}\nТелефон: {it[2]}' if len(it) == 3
            else f'Гостница: {it[0]}\nАдрес: {it[1]}\nТелефон: {it[2]}\nСсылка на сайт: {it[3]}'
            for it in spis]
    return spis


def return_in_rub(zapr):
    url = f'https://www.google.com/search?q={zapr}+рублях&sclient=gws-wiz'
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.content, 'html.parser')
    convert = soup.findAll("span", {"class": "DFlfde", "class": "SwHCTb", "data-precision": 2})
    return convert
