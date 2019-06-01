import argparse
import datetime
import logging
import multiprocessing as mp
import os
import signal
import socket
import sys
from http import HTTPStatus
from urllib.parse import unquote, urlparse

import settings


###########################################################
#                    Exception classes                    #
###########################################################

class ErrorCode(Exception):
    def __init__(self, err_code):
        super().__init__()
        self.err_code = err_code


###########################################################
#                      http handlers                      #
###########################################################


def get_file_info(path):
    try:
        res = os.path.join(os.getcwd(), os.path.normpath(path.lstrip('/')))
        if path[-1] == "/":
            res += "/"

        if not os.path.exists(res):
            raise ErrorCode(HTTPStatus.NOT_FOUND)

        if os.path.isdir(res):
            res = os.path.join(res, 'index.html')
            mime_type = settings.FILE_TYPES.get("html", None)
            if not os.path.exists(res):
                raise ErrorCode(HTTPStatus.NOT_FOUND)
        else:
            ext = path.split(".")[-1]
            mime_type = settings.FILE_TYPES.get(ext, None)
            if not mime_type:
                raise ErrorCode(HTTPStatus.FORBIDDEN)

        length = os.path.getsize(res)
    except Exception as e:
        logging.error(f"Can't find file information"
                      f" with exception {e!r}")
        raise

    return res, length, mime_type


def do_get(uri, _sock):
    path, length, mime_type = get_file_info(uri)

    with open(path, 'rb') as res:
        content = res.read()

    if length and content:
        send_response(_sock, settings.ResultingFile(
                                            content,
                                            mime_type,
                                            length),
                      HTTPStatus.OK)
    else:
        logging.error("Can't determine file length and/or content.")
        raise ErrorCode(HTTPStatus.INTERNAL_SERVER_ERROR)


def do_head(uri, _sock):
    path, length, mime_type = get_file_info(uri)

    if length:
        send_response(_sock, settings.ResultingFile(
                                                None,
                                                mime_type,
                                                length),
                      HTTPStatus.OK)
    else:
        logging.error("Can't determine file length.")
        raise ErrorCode(HTTPStatus.INTERNAL_SERVER_ERROR)

###########################################################
#                      http handlers                      #
###########################################################


def send_response(_sock, resp, state):
    ENCODING = settings.cfg['ENCODING']
    header = " ".join(("HTTP/1.0", str(state.value), state.phrase))
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z")

    if state.value == 200:
        res = settings.NORM_RESPONSE.format(
                    header=header, date=date,
                    crlf=settings.cfg['CRLF'].decode(ENCODING),
                    length=resp.length, file_type=resp.mime_type
                                            ).encode()
        if resp.content:
            res = b"".join((res, resp.content))

    else:
        res = settings.ERR_RESPONSE.format(
                            header=header, date=date,
                            crlf=settings.cfg['CRLF'].decode(ENCODING)
                                          ).encode()

    try:
        _sock.sendall(res)
    except OSError as e:
        logging.error(f"Client socket from socket{_sock} is closed"
                      f", exception is {e!r}")
    except Exception as e:
        logging.error(f"Error during send a message to socket {_sock} "
                      f"from send_error: {e!r}")
        raise
    finally:
        logging.info(f"Response sent: "
                     f"{res.split(settings.cfg['CRLF'])[0]} response")
        try:
            _sock.shutdown(socket.SHUT_RDWR)
            _sock.close()
        except Exception as e:
            logging.error(f"Error while closing a socket {e!r}")


###########################################################
#                     requests handler                    #
###########################################################


def parse_request(req, _sock):
    logging.debug("Start parsing request...")
    ENCODING = settings.cfg['ENCODING']
    CRLF = settings.cfg['CRLF']

    try:
        if not isinstance(req, str):
            raise ErrorCode(HTTPStatus.BAD_REQUEST)

        parts = req.split(CRLF.decode(ENCODING))
        parts = [line.strip() for line in parts
                 if line.strip()]
        if len(parts) < 1:
            raise ErrorCode(HTTPStatus.BAD_REQUEST)

        method, uri, protocol = parts[0].split()
        uri = unquote(urlparse(uri).path)

        if protocol not in settings.cfg['VERS']:
            raise ErrorCode(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)

    except Exception as e:
        logging.error(f"Error while parsing request: {req}")
        logging.error(f"Exception is: {e!r}")
        raise

    return method, uri


def requests_reader(_sock):
    size = 0
    buf = bytearray(settings.cfg['BUF_SIZE'])
    CRLF = settings.cfg['CRLF']
    res = None
    ENCODING = settings.cfg['ENCODING']

    while True:
        try:
            res = _sock.recv(1024)
            if not res:
                logging.error("socket is closed")
                raise ErrorCode(HTTPStatus.BAD_REQUEST)
            nbytes = len(res)
            if settings.cfg['BUF_SIZE'] >= size+nbytes:
                buf[size:size+nbytes] = res
            else:
                logging.error("Buf size too small for a message.")
                raise ErrorCode(HTTPStatus.INTERNAL_SERVER_ERROR)

            if CRLF+CRLF in buf:
                second = buf.find(CRLF, buf.find(CRLF) + len(CRLF))
                res = buf[:second + len(CRLF)].decode(ENCODING)
                logging.info(f"Start processing request: "
                             f"{res!r}")
                break
            else:
                size += nbytes
        except socket.timeout:
            logging.error(f"Connection timeout for socket {_sock}")
            raise ErrorCode(HTTPStatus.REQUEST_TIMEOUT)
        except Exception as e:
            logging.error(f"Error while handle request: {e!r}")
            raise
    return res


###########################################################
#                     starting worker                     #
###########################################################


def worker(q):
    # disable interrupting signals in processes
    s1 = signal.SIGINT
    s2 = signal.SIGTERM
    signal.pthread_sigmask(signal.SIG_BLOCK, (s1, s2))

    try:
        logging.info(f'Process {mp.current_process().name} started..')
        while True:
            _sock = q.get()
            if _sock == -1:
                break

            try:
                req = requests_reader(_sock)
                method, uri = parse_request(req, _sock)

                if method.upper() == 'GET':
                    do_get(uri, _sock)
                elif method.upper() == 'HEAD':
                    do_head(uri, _sock)
                else:
                    logging.error(f"Wrong method: {method!r}"
                                  f" in request {req!r}")
                    raise ErrorCode(HTTPStatus.METHOD_NOT_ALLOWED)
            except ErrorCode as e:
                send_response(_sock, None, e.err_code)
    except Exception as e:
        logging.error(f"Error in {mp.current_process().name} is:\n{e!r}")
        raise
    finally:
        logging.info(f"Process {mp.current_process().name} stoped.")


###########################################################
#                      https server                       #
###########################################################


def main_loop(config):
    try:
        queue = mp.Queue()
        processes = set()
        # sockets = set()

        for i in range(config.workers):
            p = mp.Process(target=worker,
                           args=(queue,))
            processes.add(p)
            p.start()

        logging.info(f'Created process pool with {config.workers} workers.')

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((config.address, config.port))
        serversocket.listen(config.workers)

        logging.info(f'Created server at address {config.address}'
                     f' and port {config.port}')

        while True:
            connectiontoclient, address = serversocket.accept()
            connectiontoclient.settimeout(settings.cfg['SOCKS_TIMEOUT'])
            queue.put(connectiontoclient)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(f"Main loop exception: /n{e!r}")
        raise
    finally:
        logging.debug("Closing processes..")
        for _ in processes:
            queue.put(-1)
        for pr in processes:
            pr.join()
        logging.debug("Closing socket..")
        try:
            serversocket.close()
        except Exception:
            pass
        logging.info("Bye Bye")


###########################################################
#             config processing and run server            #
###########################################################


def check_args(config):
    res = True

    pwd = os.path.dirname(os.path.abspath(__file__))
    cfg_folder = os.path.join(pwd, args.folder.lstrip('/'))

    if not os.path.isdir(cfg_folder):
        logging.error(f"Folder: {cfg_folder} doesn't exist")
        res = False

    if args.workers < 1:
        logging.error(f"Number of workers can not be less than 1,"
                      f" now {args.workers}")
        res = False

    return res


if __name__ == '__main__':
    logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname).1s] %(message)s',
            datefmt='%Y.%m.%d %H:%M:%S',
            stream=sys.stdout
        )

    ap = argparse.ArgumentParser()
    ap.add_argument('-a', '--address', action='store', default='127.0.0.1')
    ap.add_argument('-p', '--port', action='store', type=int, default=8080)
    ap.add_argument('-r', '--folder', action='store', default='/httptest')
    ap.add_argument('-w', '--workers', action='store', type=int, default=8)
    args = ap.parse_args()

    if check_args(args):
        try:
            main_loop(args)
        except Exception:
            raise
