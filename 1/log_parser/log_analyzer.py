#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import argparse
import sys
import logging
import string
import os
import gzip
import json
import re
from functools import reduce
from contextlib import contextmanager
from statistics import median
from string import Template
from datetime import datetime
from tempfile import NamedTemporaryFile


def load_config(cfg_file: str)->dict:
    """Loading config from a file. """
    
    config = {
            "REPORT_SIZE": 1000, 
            "REPORT_DIR": "./reports", 
            "LOG_DIR": "./log", 
            "LOG_FILE": None,  # output file for logging system
            "MIN_LINES": 0.5, 
    }    
    
    if os.path.isfile(cfg_file):
        with open(cfg_file, 'r') as f:
            for cfg in f.readlines():
                cfg = list(map(lambda x: x.strip(), cfg.split(':')))
                if cfg[0] in config.keys():
                    config[cfg[0]] = cfg[1]
                else:
                    raise ValueError("Configuration file can't be parsed")
    else:
        raise FileExistsError('Config file can not be found in the path {}'.format(args.config))
        
    return config


def date_to_int(name: str) -> int:
    '''Getting date from file name and convert it to int'''
    
    try:
        filedate = re.search(r'\d{8}', name)[0]
        
        res = int(filedate)
        
    except Exception as e:        
        logging.error(repr(e))
        raise

    return res


def date_to_str_with_delimiters(name: str)->str:
    '''Getting date from file name and converts it to a string formated "YYYY.MM.DD" '''
    
    try:
        filedate = datetime.strptime(re.search(r'\d{8}', name)[0], '%Y%m%d')        
        res = datetime.strftime(filedate, '%Y.%m.%d')
        
    except Exception as e:        
        logging.error(repr(e))
        raise

    return res

 
def get_report_name(config: dict):
    '''Return newest report file name. '''
    
    if os.path.isdir(config.get("LOG_DIR")):
        rfiles = os.listdir(config.get("LOG_DIR"))
        
        log_file = reduce(lambda acc, x: 
                           acc if date_to_int(acc) > date_to_int(x) else x
                           ,[x for x in rfiles if re.fullmatch(r'nginx-access-ui.log-\d{8}\D*', x)]
                           , 'nginx-access-ui.log-00000000')
        
        if log_file == 'nginx-access-ui.log-00000000':
            logging.error("There is no any log file in log directory (%s)" % config.get("LOG_DIR"))
            return None 
    else:
        logging.error("Log directory (%s) doesn't exist" % config.get("LOG_DIR"))
        raise FileExistsError("Log directory (%s) doesn't exist" % config.get("LOG_DIR"))
    
    log_file = os.path.join(os.path.abspath(os.getcwd()), config.get("LOG_DIR"), log_file)
    logging.info('Report file is %s' % log_file)
    return log_file


def process_line(line: str)->tuple:
    """
    Finding requested fields in line
    """  
   
    try:            
        request_time = float(re.search(r'\d{1,}\.{1}\d{0,}$', line)[0])
        request_url = re.search(r'(?<=[GET|POST]\s)(.+?)(?=\s)', line)[0]       
                                 
    except Exception as e:
        logging.error("Can't recognize line: %s"%line)
        logging.error(repr(e))
        request_time = request_url = None
        
    return request_time, request_url


def process_log_file(filepath: str, acc: list):
    '''Gathering data from log file. '''
        
    try:
        with gzip.open(filepath, 'r') \
        if filepath.split('.')[-1].lower() == 'gz' \
        else open(filepath, 'r') as f:
                    
            logging.info('open log file %s' % filepath)
                    
            for line in f:
                request_time, request_url = process_line(line.decode('utf-8'))
                acc[0] += 1
                if acc[0] == 200000: break
                if request_time and request_url:                
                    yield request_time, request_url
        logging.info('close log file') 
        
    except Exception as e:
        logging.error(repr(e))
        raise         


def logs_handler(config: dict, log_file):
    '''Logs proccessing function'''
        
    logging.info('Start proccess report file.')
   
    res = dict()
    acc = [0]
        
    for request_time, request_url in process_log_file(log_file, acc):
        if not res.get(request_url, None):
            res[request_url] = dict()
            res[request_url]['counter'] = 0
            res[request_url]['times'] = []
            
        res[request_url]['counter'] += 1
        res[request_url]['times'].append(request_time)             
    
    return res, acc

def save_to_report(config: dict, file_name: str, data: dict):
    """Saving report to 'html' file."""
    
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
        with NamedTemporaryFile('w', encoding='utf-8', dir=os.path.split(file_name)[0]) as f:        
            f.write(res)
            logging.info('Report saved to a temporary file.')
            os.link(f.name, file_name)
            logging.info('Report saved to a permanent file.')
    except FileNotFoundError:
        logging.error('Can not open file: {} for writing.'.format(file_name))
        raise

def check_report_file(config, log_file):
    '''Checking whether report file already exists. '''
    
    if not log_file:
        logging.error('Close program: there is no log file to parse')
        return
    
    logging.info('Check if report already exists')
    
    outgoing_report_name = 'report-' + date_to_str_with_delimiters(log_file) + '.html'
    outgoing_report_name = os.path.join(os.path.abspath(os.getcwd()), config['REPORT_DIR'], outgoing_report_name)
    
    if os.path.isfile(outgoing_report_name):
        logging.error("Report's already done and file is: %s Close program" % outgoing_report_name)
        return    
    
    return outgoing_report_name
    
    
def main(config: dict):
    """ Main handler function"""
        
    logging.basicConfig(filename=config.get('LOG_FILE', None), 
                        format='[%(asctime)s] %(levelname).1s %(message)s', 
                        datefmt='%Y.%m.%d %H:%M:%S', 
                        level=logging.INFO)  
    
    if not all([(i in config.keys()) for i in ["REPORT_SIZE", "REPORT_DIR", "LOG_DIR"]]):
        raise ValueError('Invalid configuration.')
    
    logging.info('Start proccessing...')
    
    try:
        log_file = get_report_name(config)
        report_file = check_report_file(config, log_file)
                
        if not report_file:
            return
        
        res, acc = logs_handler(config, log_file)
        acc = acc[0]
        
        logging.info('Log file processed. Start preparing information...')
                      
        total_requests = reduce(lambda a, x: a + x['counter'], res.values(), 0)
        total_time = reduce(lambda a, x: a + sum(x['times']), res.values(), 0)
        
        if (total_requests / acc) <  config.get('MIN_LINES', 0.5):
            logging.error("Processed less then {!s} lines of log report (now processed "
            "{!s} lines of total {!s} lines, program stopped, please, consider changing "
            "MIN_LINES config's variable (assign persentage of total lines to be processed"
            ).format(total_requests, acc, config.get('MIN_LINES', 0.5))
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
        
        save_to_report(config, report_file, data_to_save)
        
        logging.info('Task completed.')
        
    except Exception as e:
        logging.error(repr(e))
        raise     

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Parsing log files',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', nargs='?', default='./config.cfg', help='Path to a config file.')
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)        
        main(config)
    except Exception as e:
        print(repr(e))
        sys.exit(1)
        