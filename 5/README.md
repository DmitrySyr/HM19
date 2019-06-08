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
Time taken for tests:   26.483 seconds
Complete requests:      50000
Failed requests:        1
   (Connect: 0, Receive: 0, Length: 0, Exceptions: 1)
Non-2xx responses:      49999
Total transferred:      4999900 bytes
HTML transferred:       0 bytes
Requests per second:    1888.01 [#/sec] (mean)
Time per request:       52.966 [ms] (mean)
Time per request:       0.530 [ms] (mean, across all concurrent requests)
Transfer rate:          184.37 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1  37.2      0    1024
Processing:     1   51  96.3     52    6773
Waiting:        0   51  96.3     52    6773
Total:          3   53 122.7     52    7781

Percentage of the requests served within a certain time (ms)
  50%     52
  66%     53
  75%     54
  80%     54
  90%     55
  95%     55
  98%     56
  99%     57
 100%   7781 (longest request)
```

## Производительность:
В секунду обрабатывается 1888 запросов, среднее значение времени
выполнения одного запроса: 0.530 миллисекунды.

## Параметры запуска:
`-p` или `--port` указание порта
`-w` или `--workers` указание количества процессов 
`-r` или `--rootdir` указание рабочего каталога 

## Тесты
- Тесты скорректированы для работы с Python3
- Тесты запускаются стандартно (при уже запущенном сервере): 
```
python tests.py
```
