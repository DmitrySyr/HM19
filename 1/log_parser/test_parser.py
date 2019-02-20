"""
    Testing the log parser.
"""
import unittest
import tempfile
import os

import log_analyzer


class TestLogger(unittest.TestCase):
    
    def test_load_config_good(self):
        with tempfile.NamedTemporaryFile(mode = 'w+', encoding = 'utf-8') as f:
            cfg_path = f.name
            f.write('REPORT_DIR: ./rp')
            f.seek(0)
            
            config = log_analyzer.load_config(cfg_path)
            
            config_etalon = {
            "REPORT_SIZE": 1000
            , "REPORT_DIR": "./rp"
            , "LOG_DIR": "./log"
            , "LOG_FILE": None #output file for logging system
            , "MIN_LINES": 0.5
            }      
                              
            self.assertDictEqual(config, config_etalon)
    def test_load_config_good_with_empty_parameter(self):
        
        config = log_analyzer.load_config('./config.cfg')
        
        config_etalon = {
            "REPORT_SIZE": 1000
            , "REPORT_DIR": "./reports"
            , "LOG_DIR": "./log"
            , "LOG_FILE": None #output file for logging system
            , "MIN_LINES": 0.5
        }    
        
        self.assertDictEqual(config, config_etalon)    
    
    def test_load_config_bas_parsing(self):
        with tempfile.NamedTemporaryFile(mode = 'w+', encoding = 'utf-8') as f:
            cfg_path = f.name
            f.write('REPORT_DIR_BAD: ./rp')
            f.seek(0)
            
            with self.assertRaises(ValueError):
                config = log_analyzer.load_config(cfg_path)
    
    def test_load_config_no_file(self):
        
        with tempfile.NamedTemporaryFile(mode = 'w+', encoding = 'utf-8') as f:
            cfg_path = f.name + '.bad'
            
            with self.assertRaises(Exception):
                config = log_analyzer.load_config(cfg_path)
    
    def test_dateToInt__good(self):
        name = 'nginx-access-ui.log-20170630.gz'
        
        date_int = log_analyzer.date_to_int(name)
        
        self.assertEqual(date_int, 20170630)
    
    def test_dateToInt__bad(self):
        name = 'nginx-access-ui.log-201d0630.gz'
        
        with self.assertRaises(Exception):
            date_int = log_analyzer.date_to_int(name) 
            
    def test_dateToStrWithDelimiters__good(self):
        name = 'nginx-access-ui.log-20170630.gz'
        
        date_delimited = log_analyzer.date_to_str_with_delimiters(name)
        
        self.assertEqual(date_delimited, '2017.06.30')
    
    def test_dateToStrWithDelimiters__bad_too_short(self):
        name = 'nginx-access-ui.log-201630.gz'
        
        with self.assertRaises(Exception):
            date_delimited = log_analyzer.date_to_str_with_delimiters(name)               

    def test_dateToStrWithDelimiters__bad_wrong_date(self):
        name = 'nginx-access-ui.log-2016d30.gz'
        
        with self.assertRaises(Exception):
            date_delimited = log_analyzer.date_to_str_with_delimiters(name)         
    
    def test_get_report_name___good(self):
        config = log_analyzer.load_config('./config.cfg')
        config['LOG_DIR'] = files_path = os.path.abspath(os.getcwd())
        
        file_list = [os.path.join(files_path, x) for x in ['nginx-access-ui.log-20120208.gz'
                                                           , 'nginx-access-ui.log-20120212.gz'
                                                           , 'nginx-access-ui.log-20110308.gz'
                                                           , 'nginx-access-ui.log-20121201.gz']]
        
        try:
            for file_name in file_list:
                f = open(file_name, mode='w')
                f.write('abc')
                f.close()
                
            choosen_log_file = log_analyzer.get_report_name(config)
            choosen_log_file = choosen_log_file.split('/')[-1]
            
            self.assertEqual(choosen_log_file, 'nginx-access-ui.log-20121201.gz')
        finally:
            for f in file_list:
                os.remove(f)
                
    def test_get_report_name___good_no_file(self):
        config = log_analyzer.load_config('./config.cfg')
        config['LOG_DIR'] = files_path = os.path.abspath(os.getcwd())
        
        choosen_log_file = log_analyzer.get_report_name(config)
            
        self.assertEqual(choosen_log_file, None)
         
    def test_get_report_name___good_bad_file_doesnt_exist(self):
        config = log_analyzer.load_config('./config.cfg')
        config['LOG_DIR'] = os.path.join(os.path.abspath(os.getcwd()))
                
        choosen_log_file = log_analyzer.get_report_name(config)
            
        self.assertEqual(choosen_log_file, None)    
    
    def test_process_line__good(self):
        input_string = '1.196.116.32 -  - [29/Jun/2017:03:52:22 +0300] "GET /api/v2/banner/24852159 HTTP/1.1" \
        200 976 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" \
        "1498697540-2190034393-4709-9930664" "dc7161be3" 1.390'
        
        request_time, request_url = log_analyzer.process_line(input_string)
        
        self.assertEqual((request_time, request_url), (1.39, "/api/v2/banner/24852159"))
        
        
    def test_process_line__good_post(self):
        input_string = '1.196.116.32 -  - [29/Jun/2017:03:52:22 +0300] "POST /api/v2/banner/24852159 HTTP/1.1" \
        200 976 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" \
        "1498697540-2190034393-4709-9930664" "dc7161be3" 1.390'
        
        request_time, request_url = log_analyzer.process_line(input_string)
        
        self.assertEqual((request_time, request_url), (1.39, "/api/v2/banner/24852159"))        
    
    
    def test_process_line__bad_bad_date(self):
        input_string = '1.196.116.32 -  - [29/Jun/2017:03:52:22 +0300] "GET /api/v2/banner/24852159 HTTP/1.1" \
        200 976 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" \
        "1498697540-2190034393-4709-9930664" "dc7161be3"'
        
        request_time, request_url = log_analyzer.process_line(input_string)
        
        self.assertEqual((request_time, request_url), (None, None))
        
    def test_process_line__bad_no_request(self):
        input_string = '1.196.116.32 -  - [29/Jun/2017:03:52:22 +0300] \
        200 976 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" \
        "1498697540-2190034393-4709-9930664" "dc7161be3"'
        
        request_time, request_url = log_analyzer.process_line(input_string)
        
        self.assertEqual((request_time, request_url), (None, None))        
        
if __name__ == '__main__':
        unittest.main()