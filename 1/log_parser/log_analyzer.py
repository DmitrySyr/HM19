#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import sys
import logging
import string
import os
import gzip
import json
from functools import reduce
from contextlib import contextmanager
from statistics import median
from string import Template

def load_config(cfg_path='')->dict:
    """
    Loading config from a file
    """
    config = {
            "REPORT_SIZE": 1000
            , "REPORT_DIR": "./reports"
            , "LOG_DIR": "./log"
            , "LOG_FILE": None #output file for logging system
            , "MIN_LINES": 0.5
    }    
    
    if cfg_path != '':
        with open(cfg_path, 'r') as f:
            for cfg in f.readlines():
                cfg = list(map(lambda x: x.strip(), cfg.split(':')))
                if cfg[0] in config.keys():
                    config[cfg[0]] = cfg[1]
                else:
                    logging.error("Configuration file can't be parsed")
                    raise ValueError  
    return config

def dateToInt(name: str) -> int:
    '''
    Getting date from file name and convert it to int
    '''
    try:
        filedate = name.split('-')[-1].split('.')[0]
        
        res = int(filedate)
        
    except Exception as e:        
        logging.error(repr(e))
        raise

    return res

def dateToStrWithDelimiters(name: str)->str:
    '''
    Getting date from file name and converts it to a string formated "YYYY.MM.DD"
    '''
    try:
        filedate = name.split('-')[-1].split('.')[0]
        
        if len(filedate) != 8:
            raise ValueError('Wrong log file name.')
        
        # check if it's a number
        res = int(filedate)
        
        res = ".".join([filedate[:4], filedate[4:6], filedate[6:]])
        
    except Exception as e:        
        logging.error(repr(e))
        raise

    return res
 
def get_report_name(config: dict):
    '''
    Return newest report file name
    '''
    if os.path.isdir(config.get("LOG_DIR")):
        rfiles = os.listdir(config.get("LOG_DIR"))
        
        log_file = reduce(lambda acc, x: 
                           acc if dateToInt(acc) > dateToInt(x) else x
                           ,[x for x in rfiles if x.startswith('nginx-access-ui.log-')]
                           , 'nginx-access-ui.log-00000000')
        
        if log_file == 'nginx-access-ui.log-00000000':
            logging.error("There is no any log file in log directory (%s)" % config.get("LOG_DIR"))
            return None 
    else:
        logging.error("Log directory (%s) doesn't exist" % config.get("LOG_DIR"))
        return None
    
    logging.info('Report file is %s' % log_file)
    return log_file

def process_line(line: str)->tuple:
    """
    Finding requested fields in line
    """  
   
    try:
        request_time = float(line.split()[-1].strip())
        request_url = [x for x in line.split('"') if (x.startswith('GET')) | (x.startswith('POST'))][0]
    except Exception as e:
        logging.error("Can't recognize line: %s"%line)
        logging.error(repr(e))
        request_time = request_url = None
        
    return request_time, request_url


def process_log_file(filepath: str, acc: list):
    '''
    Gathering data from log file
    '''
        
    try:
        ext = filepath.split('.')[-1].lower()
                
        if ext == 'gz':
            f = gzip.open(filepath, 'r')
        else:
            f = open(filepath, 'r')
            
        logging.info('open log file %s' % filepath)
        
        
        for line in f:
            request_time, request_url = process_line(line.decode('utf-8'))
            acc[0] += 1
            if acc[0] == 200000: break
            if request_time and request_url:                
                yield request_time, request_url
            
                
    except Exception as e:
        logging.error(repr(e))
        raise
    finally:
        f.close()
        logging.info('close log file')

def logs_handler(config: dict):
    '''
    Main proccessing function
    '''
    
    logging.info('Start proccessing...')
    
    logging.info('Collect report file name')
    
    if not all( [(i in config.keys()) for i in ["REPORT_SIZE", "REPORT_DIR", "LOG_DIR"]] ):
        raise ValueError('Invalid configuration.')
    
    log_file = get_report_name(config)
    
    if not log_file:
        logging.error('Close program: there is no log file to parse')
        return
    
    logging.info('Check if report already exists')
    
    outgoing_report_name = 'report-' + dateToStrWithDelimiters(log_file) + '.html'
    outgoing_report_name = os.path.join(os.path.abspath(os.getcwd()), config['REPORT_DIR'], outgoing_report_name)
    
    if os.path.isfile(outgoing_report_name):
        logging.info("Report's already done and file is: %s Close program" % outgoing_report_name)
        return
   
    logging.info('Start proccess report file.')
   
    log_file = os.path.join(os.path.abspath(os.getcwd()), config["LOG_DIR"], log_file)
    
    res = dict()
    acc = [0]
        
    for request_time, request_url in process_log_file(log_file, acc):
        if not res.get(request_url, None):
            res[request_url] = dict()
            
        res[request_url]['counter'] = res[request_url].get('counter', 0) + 1
        res[request_url]['times'] = res[request_url].get('times', []) + [request_time]                
    
    return res, outgoing_report_name, acc

def save_to_report(config: dict, fileName: str, data: dict):
    """
        Saving report to 'html' file.
    """
    res = sorted(data, key = lambda x: x['time_sum'], reverse=True)[:config['REPORT_SIZE']]      
    
    try:
        with open(config.get('HTML_TPL', 'report.html'), mode='r', encoding='utf-8') as f:
            html = f.read()
            template = Template(html)
            res = template.safe_substitute(table_json=json.dumps(res))
                            
    except FileNotFoundError:
        logging.error('There is no template html file.')
        raise

        
    try:
        with open(fileName, mode='w', encoding='utf-8') as f:
            f.write(res)
            logging.info('Report saved to a file.')
    except FileNotFoundError:
        logging.error('Can not open file: {} for writing.'.format(fileName))
        raise


def main():
    
    if (len(sys.argv) == 3) & (sys.argv[1] == '--config'):
        cfg_path = sys.argv[2]
        
        try:
            config = load_config(cfg_path)
        except FileNotFoundError:
            t, i, t = sys.exc_info()
            logging.exception('Configuration file opening error %s: %s' % (i.filename, i.strerror))
            sys.exit(1)    
        except Exception as e:
            logging.exception(repr(e))        
            sys.exit(1)    
        
    logging.basicConfig(filename = config.get('LOG_FILE', None) 
                        , format = '[%(asctime)s] %(levelname).1s %(message)s'
                        , datefmt = '%Y.%m.%d %H:%M:%S'
                        , level = logging.INFO)       
    try:
        res, report_name, acc = logs_handler(config)
        acc = acc[0]
        
        logging.info('Log file processed. Start preparing information...')
                      
        total_requests = reduce(lambda a, x: a + x['counter'], res.values(), 0)
        total_time = reduce(lambda a, x: a + sum(x['times']), res.values(), 0)
        
        if (total_requests / acc) <  config.get('MIN_LINES', 0.5):
            logging.error("Processed less then {!s} lines of log report, program stopped, \
            please, consider changing MIN_LINES config's variable (assign persentage of \
            total lines to be processed).".format(config.get('MIN_LINES', 0.5)))
            raise ValueError
        
        data_to_save = []
        for req, val in res.items():
            line = dict()
            line['request'] = req
            line['counter'] = val['counter']
            line['count_perc'] = round((val['counter'] / total_requests) * 100, 3)
            line['time_sum'] = round(sum(val['times']), 3)
            line['time_perc'] = round((line['time_sum'] / total_time) * 100, 3)
            line['time_avg'] = round(line['time_sum'] / len(val['times']), 3)
            line['time_max'] = round(max(val['times']), 3)
            line['time_med'] = round(median(val['times']), 3)
            
            data_to_save.append(line)
            
        logging.info('Information prepared. Start saving to report...')
        
        save_to_report(config, report_name, data_to_save)
        
        logging.info('Work completed.')
        
    except Exception as e:
        logging.exception(repr(e))        
        sys.exit(1)     

if __name__ == "__main__":
    main()
        