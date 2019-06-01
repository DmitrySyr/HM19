# OTUS. Задание №5
## веб‐сервер с частичной реализацией протокола HTTP
Архитектура: синхронный сервер масштабирующийся на n процессов
Особенности:
 - Python 3.6.8
 - при запуске создаётся набор процессов
 - соединения принимаются синхронно в основном потоке и передаются процессам на обработку
 - поддерживаются методы GET и HEAD
 - взаимодействие между процессами-обработчиками и основным
реализованы через стандартную Queue из Multiprocessing
 - основные найстройки вынесены в settings.py

## Результаты нагрузочного тестирования
Нагрузочное тестирование утилитой *Apache Benchmark*

### Параметры:
*Количество процессов-обработчиков: *8**
*Количество запросов: *50000**
*Количество конкурентных запросов: *100**

### Результаты:
```
Server Software:        Python
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   39.046 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      49999
Total transferred:      4999900 bytes
HTML transferred:       0 bytes
Requests per second:    1280.55 [#/sec] (mean)
Time per request:       78.091 [ms] (mean)
Time per request:       0.781 [ms] (mean, across all concurrent requests)
Transfer rate:          125.05 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    3  53.7      0    1029
Processing:     4   75 295.4     71   26757
Waiting:        0   75 295.4     71   26757
Total:          5   78 322.0     71   27781

Percentage of the requests served within a certain time (ms)
  50%     71
  66%     75
  75%     79
  80%     81
  90%     89
  95%     99
  98%    109
  99%    126
 100%  27781 (longest request)
```

## Производительность:
В секунду обрабатывается 1280 запросов, среднее медианное значение времени
выполнения одного запроса: 0.781 миллисекунды.

## Параметры запуска:
`-p` или `--port` указание порта
`-w` или `--workers` указаниу количества процессов 
`-r` или `--rootdir` указание рабочего каталога 

## Тесты
- Тесты скорректированы для работы с Python3
- Тесты запускаются стандартно (при уже запущенном сервере): 
```
python tests.py
```
