slov = {}
with open('cities_codes.txt', encoding='UTF-8') as file:
    for line in file:
        lin = line.split(',')
        slov[lin[1][1:-2]] = int(lin[0])


def return_code(city):
    return slov[city]
