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
Time taken for tests:   24.991 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5000000 bytes
HTML transferred:       0 bytes
Requests per second:    2000.74 [#/sec] (mean)
Time per request:       49.981 [ms] (mean)
Time per request:       0.500 [ms] (mean, across all concurrent requests)
Transfer rate:          195.39 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    3  52.8      0    1032
Processing:     4   47  91.6     47    6866
Waiting:        4   47  91.6     47    6866
Total:          6   50 123.5     47    7870

Percentage of the requests served within a certain time (ms)
  50%     47
  66%     49
  75%     49
  80%     50
  90%     53
  95%     57
  98%     62
  99%     73
 100%   7870 (longest request)
```

## Производительность:
В секунду обрабатывается 2000 запросов, среднее медианное значение времени
выполнения одного запроса: 0.5 миллисекунды.

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
