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
#                      http handlers                      #
###########################################################


def get_file_path(path):
    res = os.path.join(os.getcwd(), os.path.normpath(path.lstrip('/')))\
          + ("/" if path[-1] == "/" else "")

    if not os.path.exists(res):
        return None

    if os.path.isdir(res):
        res = os.path.join(res, 'index.html')
        if not os.path.exists(res):
            return None
    return res


def do_get(uri, _sock):
    path = get_file_path(uri)

    if not path:
        send_response(_sock, None, HTTPStatus.NOT_FOUND)
        return

    ext = path.split(".")[-1]
    mime_type = settings.FILE_TYPES.get(ext, None)

    if not mime_type:
        send_response(_sock, None, HTTPStatus.FORBIDDEN)
        return

    length = os.path.getsize(path)

    with open(path, 'rb') as res:
        content = res.read()

    if length and content:
        send_response(_sock, settings.ResultingFile(content, ext, length),
                      HTTPStatus.OK)
    else:
        raise Exception("Can't determine file length and/or content.")


def do_head(uri, _sock):
    path = get_file_path(uri)

    if not path:
        send_response(_sock, None, HTTPStatus.NOT_FOUND)
        return

    ext = path.split(".")[-1]
    if ext not in settings.FILE_TYPES:
        send_response(_sock, None, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        return

    length = os.path.getsize(path)

    if length:
        send_response(_sock, settings.ResultingFile(None, ext, length),
                      HTTPStatus.OK)
    else:
        raise Exception("Can't determine file length.")

###########################################################
#                      http handlers                      #
###########################################################


def send_response(_sock, resp, state):
    header = " ".join(("HTTP/1.0", str(state.value), state.phrase))
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z")

    if state.value == 200:
        res = settings.NORM_RESPONSE.format(
            header=header, date=date, crlf=settings.cfg['CRLF'].decode(),
            length=resp.length, file_type=settings.FILE_TYPES[resp.extention]
                                            ).encode()
        if resp.content:
            res = b"".join((res, resp.content))

    else:
        res = settings.ERR_RESPONSE.format(
            header=header, date=date, crlf=settings.cfg['CRLF'].decode()
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


def method_handler(method, uri, _sock):
    try:
        if method.upper() == 'GET':
            do_get(uri, _sock)
        elif method.upper() == 'HEAD':
            do_head(uri, _sock)
        else:
            send_response(_sock, None, HTTPStatus.METHOD_NOT_ALLOWED)
    except Exception:
        raise


###########################################################
#                     requests handler                    #
###########################################################


def parse_request(req, _sock):
    logging.debug("Start parsing request...")
    ENCODING = settings.cfg['ENCODING']
    CRLF = settings.cfg['CRLF']

    try:
        parts = req.split(CRLF)
        parts = [line.strip().decode(ENCODING) for line in parts
                 if line.strip()]
        if len(parts) < 1:
            send_response(_sock, None, HTTPStatus.BAD_REQUEST)
            return

        method, uri, protocol = parts[0].split()
        uri = unquote(urlparse(uri).path)
    except Exception as e:
        logging.error(f"{e!r}")
        send_response(_sock, None, HTTPStatus.BAD_REQUEST)
        return

    if protocol not in settings.cfg['VERS']:
        send_response(_sock, None, HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)
        return

    try:
        method_handler(method, uri, _sock)
    except Exception as e:
        logging.error(f"{e!r}")
        send_response(_sock, None, HTTPStatus.INTERNAL_SERVER_ERROR)
        return


def requests_reader(_sock):
    size = 0
    buf = bytearray(settings.cfg['BUF_SIZE'])
    CRLF = settings.cfg['CRLF']

    while True:
        try:
            res = _sock.recv(1024)
            if not res:
                # socket is closed
                break
            nbytes = len(res)
            buf[size:size+nbytes] = res

            if CRLF+CRLF in buf:
                second = buf.find(CRLF, buf.find(CRLF) + len(CRLF))
                logging.info(f"Start processing request: "
                             f"{buf[:second + len(CRLF)]}")
                parse_request(buf[:second + len(CRLF)], _sock)
                break
            else:
                size += nbytes
        except BlockingIOError as e:
            logging.error(f"{e!r}")
        except socket.timeout:
            logging.error(f"Connection timeout for socket {_sock}")
            send_response(_sock, None, HTTPStatus.REQUEST_TIMEOUT)
        except OSError as e:
            logging.error(f"{e!r}")
        except Exception as e:
            logging.error(f"{e!r}")
            raise
        finally:
            try:
                _sock.shutdown(socket.SHUT_RDWR)
                _sock.close()
            except Exception as e:
                logging.error(f"Error while closing a socket {e!r}")
            break


###########################################################
#                     starting worker                     #
###########################################################


def reading_queue(q):
    try:
        while True:
            f = q.get()
            if f == -1:
                break
            requests_reader(f)
    except Exception as e:
        logging.error(f"In reading queue in process "
                      f"{mp.current_process().name}"
                      f" error is {e!r}")
        raise


def worker(q):
    # disable interrupting signals in processes
    s1 = signal.SIGINT
    s2 = signal.SIGTERM
    signal.pthread_sigmask(signal.SIG_BLOCK, (s1, s2))

    try:
        logging.info(f'Process {mp.current_process().name} started..')
        reading_queue(q)
        # loop.run_forever()
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
