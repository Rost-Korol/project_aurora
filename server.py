from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
import smtplib

app = Flask(__name__)


@app.route("/")
def home():
    # Парсим данные K индекса
    aurora_village = "https://auroravillage.info/ru/forecast/"
    # res = requests.get(url="https://services.swpc.noaa.gov/text/27-day-outlook.txt")
    res = requests.get(url=aurora_village)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_stuff = soup.find_all(name="span", class_="__kpi")
    progress_date = soup.select(".progress-aurora")
    now = datetime.today()
    my_now = now.strftime('%b %d')

    # Сегодня +7 дней
    dates_list = []
    for i in range(8):
        next_day = now + timedelta(days=i)
        dates_list.append(next_day.strftime('%b %d'))

    # Словарь с К индексами
    k_dict = {}
    for tag in progress_date:
        a = tag.text.split()
        if len(a[0]) == 3:
            month = a[0]
            day = a[1][0:2]
            k_index = a[1][2]
            date = month + " " + day
            k_dict[date] = k_index

    # Делаем запрос погоды с openweather
    with open('api_key.txt', 'r') as file:
        api_key = file.read()
    longitude = 76.6333
    latitude = 66.0833
    parameters = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "exclude": "current, minutely, hourly",
        "units": "metric",
    }

    res2 = requests.get("https://api.openweathermap.org/data/2.5/onecall", params=parameters)
    res2.raise_for_status()
    weather_data = res2.json()

    # Создаем словарь с данными по рассвету и закату
    dark_dict = {}
    for i in range(8):
        sunset = weather_data['daily'][i]['sunset']
        sunrise = weather_data['daily'][i]['sunrise']
        day = weather_data['daily'][i]['dt']
        sunset_hour = datetime.utcfromtimestamp(float(sunset)) + timedelta(hours=5)
        sunset_hour = sunset_hour.strftime("%H:%M")
        sunrise_hour = datetime.utcfromtimestamp(float(sunrise)) + timedelta(hours=5)
        sunrise_hour = sunrise_hour.strftime("%H:%M")
        day = datetime.utcfromtimestamp(float(day))
        day = day.strftime('%b %d')
        dict1 = {}
        dict1['Sunrise'] = sunrise_hour
        dict1['Sunset'] = sunset_hour
        dark_dict[day] = dict1
    # словарь с именами значков погоды
    id_dict = {}
    for i in weather_data['daily']:
        time1 = datetime.utcfromtimestamp(i['dt']) + timedelta(hours=5)
        time1 = time1.strftime('%b %d')
        id_dict[time1] = i['weather'][0]['icon']

    # погода сейчас
    for i in weather_data['hourly']:
        now_day = now.day
        now_hour = now.hour
        w_day = (datetime.utcfromtimestamp(float(i['dt'])) + timedelta(hours=2)).day
        w_hour = (datetime.utcfromtimestamp(float(i['dt'])) + timedelta(hours=2)).hour
        if now_day == w_day and now_hour == w_hour:
            now_temp = (round(i['temp'], 1))
            now_id = i['weather'][0]['icon']

    # # Код для рассылки
    # clouds_keys = {}  # 800 - clear_sky; 801 - few clouds
    # for i in range(8):
    #     weather_id = weather_data['daily'][i]['weather'][0]['id']
    #     day = weather_data['daily'][i]['dt']
    #     day = datetime.utcfromtimestamp(float(day))
    #     day = day.strftime('%b %d')
    #     clouds_keys[day] = weather_id
    # print(clouds_keys)
    #
    # datetime.hour
    # my_email = "my.email.sender@gmail.com"  # Нужно зарегать email
    # # и снять в нем все запреты для удаленного доступа кода
    # password = "*********"  # - пароль))
    # hour_now = (now + timedelta(hours=5)).hour
    # mails_dict = {"example@mail.ru", "someone@gmail.com"} # Нужно как то брать этот список из подписавшихся
    # # на сайте
    # if hour_now == 0: # В 12 ночи
    #     if k_dict[now.day] >= 4: # Провряем есть ли геомагнитные бури сегодня
    #         if hour_now <= sunset or hour_now >= sunrise: # проверяем когда сегодня будет темно
    #             if clouds_keys[now.day] == 800 or clouds_keys[now.day] == 801: # будет ли ясное небо (надо переделать
    #                 # на почасовую погоду когда темно)
    #                 connection = smtplib.SMTP("smtp.gmail.com")
    #                 connection.starttls()
    #                 connection.login(user=my_email, password=password)
    #
    #                 for adress in mails_dict:
    #                     connection.sendmail(from_addr=my_email,
    #                                         to_addrs=adress,
    #                                         msg=f"Северное сияние\n\n Сегодня можно будет увидеть северное сияния!")
    #                     connection.close()
    # time.sleep(60 * 60)

    return render_template("index.html", k_dict=k_dict, dates_list=dates_list, id_dict=id_dict, dark_dict=dark_dict,
                           now_temp=now_temp, now_id=now_id)


if __name__ == "__main__":
    #app.run(debug=True)
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
