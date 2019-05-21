from collections import namedtuple

cfg = {
    'CRLF': b'\r\n',
    'ENCODING': 'utf-8',
    'VERS': ('HTTP/1.1', 'HTTP/1.0'),
    'methods': ('GET', 'HEAD'),
    'BUF_SIZE': 2048,
    'SOCKS_TIMEOUT': 5.0,
}

ResultingFile = namedtuple('ResultingFile',
                               ['content', 'extention', 'length'])

FILE_TYPES = {'html': 'text/html',
              'css': 'text/css',
              'txt': 'text/plain',
              'js': 'text/javascript',
              'jpg': 'image/jpeg',
              'jpeg': 'image/jpeg',
              'png': 'image/png',
              'gif': 'image/gif',
              'swf': 'application/x-shockwave-flash'}

NORM_RESPONSE = "{header}{crlf}" \
                "Date: {date}{crlf}" \
                "Server: Python Otus{crlf}" \
                "Content-Length: {length}{crlf}" \
                "Connection: close{crlf}" \
                "Content-Type: {file_type}{crlf}{crlf}"

ERR_RESPONSE = ("{header}{crlf}"
                "Date: {date}{crlf}"
                "Server: Python Otus{crlf}"
                "Connection: close{crlf}{crlf}")
