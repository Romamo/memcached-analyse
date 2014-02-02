#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Чем заполнена ваша память или анализатор использования memcached

Отчеты позволяют получить ответы на следующие вопросы:
Какими именно данными (ключами) заполнена память?
Какие группы ключей имеют низкий хиттинг?

Порядок получения необходимых данных
1. Запустить memcached -vv -u nobody 2>access.txt на необходимый период времени, в течение которого будет осуществляться типовые операции с memcached
2. После завершения логирования получить дамп содержимого памяти memcached-tool localhost:11211 dump | grep "add " > dump.txt

Будьте уверены, что закэшированные данные в memcached не просрочены в момент дампа.
В случае, если ключ отсутствует

Также возможны две стратегии для анализа.
1. Снятие данных при старте
2. Снятие данных при

touch /var/log/memcached.log; chmod 0666 /var/log/memcached.log
ee /usr/local/etc/rc.d/memcached

command_args="-d -u ${memcached_user} -P ${pidfile} -vv 2>/var/log/memcached.log"

/usr/local/etc/rc.d/memcached restart


/usr/local/etc/rc.d/memcached stop; memcached -m 2000 -vv -u nobody 2>access.txt
/usr/local/etc/rc.d/memcached start

cat access.txt | ./analyse.py
cat memcached.log | ./analyse.py

Учитываются только уникальные ключи

Для анализа программе необходимы 2 лога:
1. Дамп списка ключей
2. Лог запросов к memcached за определенный период времени

logfile 30Gb
Processed lines: 2945320000 Keys: 401196
Время: около часа
json: 44mb

# memcached-tool localhost:11211 dump | grep "add " > dump.txt


1. Получить лог файл memcached
# memcached -vv -u nobody 2>access.txt

2. Просмотр ключей и настройка групп
python analyse.py --settings=settings-sample --input-file=memcached.log --limit-lines=10000000 --no-progress --print-keys |more
cp settings-sampe.py settings-my.py
ee settings-my.py
Добавляем свои шаблоны в PATTERN_GROUP и PATTERN_KEY
Вначале используются шаблоны группы, затем ключей
Когда результат группировки станет вас удовлетворять, переходим к следующему шагу

3. Анализ лог файла и создание файла с данными статистики
python analyse.py --use-file=analyse.json --settings=settings-sample --input-file=memcached.log --limit-lines=10000
Ваш много гигабайтный лог файл будет обработан и проанализированные данные о ключах и группах будут записаны в файл analyse.json

4. Генерация отчетов, используя файл с данными
python  analyse.py --use-file=analyse.json --settings=settings-sample --report=g:size:100 |more
# Самые прожорливые группы
python  analyse.py --use-file=analyse.json --settings=settings-sample --report=g:size:100 |more

Далее долго изучаем все отчеты, обращаем внимание на низкий hitrate, потребление памяти, высокий miss и hit, нулевой set и принимаем решения:
отправить на рефакторинг код работы с определеенным кючом
отключить вообще кеширование определенных данных по причине низкой эффективности



"""

import argparse
from parser import Parser
from reports import Reports

parser = argparse.ArgumentParser(description='Analyse memcached logs')
#parser.add_argument('--report', dest='report', action='store_const',
#                   default=max,
#                   help='sum the integers (default: find the max)')
parser.add_argument('--input-file', dest='input_file', action='store', default='', help='path to memcached log file')
parser.add_argument('--limit-lines', dest='limit_lines', action='store', default=0, help='limit lines to process')
parser.add_argument('--use-file', dest='use_file', action='store', default=None, help='use file to store analyzed data')
parser.add_argument('--settings', dest='settings', action='store', default='settings', help='settings file')
parser.add_argument('--reports', dest='reports', action='store', default=None, help='show reports')
parser.add_argument('--no-progress', dest='print_progress', action='store_false', default=True, help='show progress')
parser.add_argument('--print-keys', dest='print_keys', action='store_true', default=False, help='print keys')
parser.add_argument('--groups', dest='groups', action='store', default=None, help='filter keys to groups list separated by comma(,)')

args = parser.parse_args()


settings_file = args.settings or 'settings'
settings = __import__(settings_file, {}, {}, [])

p = Parser(settings, {'print_progress': args.print_progress, 'print_keys': args.print_keys})

if args.input_file:
    p.parse(args.input_file, int(args.limit_lines))

    if args.use_file:
        p.save_data(args.use_file)

    r = Reports(settings, {'groups': args.groups and args.groups.split(',')}, p.get_data())
else:
    r = Reports(settings, {'groups': args.groups and args.groups.split(',')}, args.use_file)

r.main(args.reports)


#import memcache
#mc = memcache.Client(['127.0.0.1:11211'], debug=0)
#print mc.get_stats()
