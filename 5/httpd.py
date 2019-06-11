import argparse
import datetime
import logging
import multiprocessing as mp
import os
import socket
import sys
from http import HTTPStatus
from urllib.parse import unquote, urlparse

import settings


###########################################################
#     Exception classes and global variables              #
###########################################################


FIN_QUEUE = -1

class ErrorCode(Exception):
    def __init__(self, err_code):
        super().__init__()
        self.err_code = err_code


###########################################################
#                      http handlers                      #
###########################################################


def get_file_info(path):
    res = os.path.join(os.getcwd(), os.path.normpath(path.lstrip("/")))
    if path[-1] == "/":
        res += "/"

    if not os.path.exists(res):
        raise ErrorCode(HTTPStatus.NOT_FOUND)

    if os.path.isdir(res):
        res = os.path.join(res, "index.html")
        mime_type = settings.FILE_TYPES.get("html", None)
        if not os.path.exists(res):
            raise ErrorCode(HTTPStatus.NOT_FOUND)
    else:
        ext = path.split(".")[-1]
        mime_type = settings.FILE_TYPES.get(ext, None)
        if not mime_type:
            raise ErrorCode(HTTPStatus.FORBIDDEN)

    length = os.path.getsize(res)
    return res, length, mime_type


def do_get(uri, _sock):
    path, length, mime_type = get_file_info(uri)

    with open(path, "rb") as res:
        content = res.read()

    if length and content:
        send_response(
            _sock, settings.ResultingFile(content, mime_type, length), HTTPStatus.OK
        )
    else:
        logging.error("Can't determine file length and/or content.")
        raise ErrorCode(HTTPStatus.INTERNAL_SERVER_ERROR)


def do_head(uri, _sock):
    path, length, mime_type = get_file_info(uri)

    if length:
        send_response(
            _sock, settings.ResultingFile(None, mime_type, length), HTTPStatus.OK
        )
    else:
        logging.error("Can't determine file length.")
        raise ErrorCode(HTTPStatus.INTERNAL_SERVER_ERROR)


###########################################################
#                      http handlers                      #
###########################################################


def send_response(_sock, resp, state):
    ENCODING = settings.cfg["ENCODING"]
    header = " ".join(("HTTP/1.0", str(state.value), state.phrase))
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z")

    if state.value == 200:
        res = settings.NORM_RESPONSE.format(
            header=header,
            date=date,
            crlf=settings.cfg["CRLF"].decode(ENCODING),
            length=resp.length,
            file_type=resp.mime_type,
        ).encode()
        if resp.content:
            res = b"".join((res, resp.content))

    else:
        res = settings.ERR_RESPONSE.format(
            header=header, date=date, crlf=settings.cfg["CRLF"].decode(ENCODING)
        ).encode()

    try:
        _sock.sendall(res)
    except OSError as e:
        logging.error(
            f"Client socket from socket{_sock} is closed, exception is {e!r}"
        )
    finally:
        logging.info(
            f"Response sent: {res.split(settings.cfg['CRLF'])[0]} response"
        )
        try:
            _sock.shutdown(socket.SHUT_RDWR)
            _sock.close()
        except Exception as e:
            logging.error(f"Error while closing a socket {e!r}")


###########################################################
#                     requests handler                    #
###########################################################


def parse_request(req):
    logging.debug("Start parsing request...")
    ENCODING = settings.cfg["ENCODING"]
    CRLF = settings.cfg["CRLF"]

    if not isinstance(req, str):
        raise ErrorCode(HTTPStatus.BAD_REQUEST)

    parts = req.split(CRLF.decode(ENCODING))
    parts = [line.strip() for line in parts if line.strip()]
    if len(parts) < 1:
        raise ErrorCode(HTTPStatus.BAD_REQUEST)

    method, uri, protocol = parts[0].split()
    uri = unquote(urlparse(uri).path)

    if protocol not in settings.cfg["VERS"]:
        raise ErrorCode(HTTPStatus.HTTP_VERSION_NOT_SUPPORTED)
    return method, uri


def requests_reader(_sock):
    buf = b""
    CRLF = settings.cfg["CRLF"]
    res = None
    ENCODING = settings.cfg["ENCODING"]

    while True:
        try:
            res = _sock.recv(1024)
            if not res:
                logging.error("socket is closed")
                return None
            buf += res
            if CRLF + CRLF in buf:
                res = buf.decode(ENCODING)
                logging.info(f"Start processing request: {res!r}")
                break
        except socket.timeout:
            logging.error(f"Connection timeout for socket {_sock}")
            raise ErrorCode(HTTPStatus.REQUEST_TIMEOUT)
    return res


###########################################################
#                     starting worker                     #
###########################################################


def worker(q):
    try:
        logging.info(f"Process {mp.current_process().name} started..")
        while True:
            _sock = q.get()
            if _sock == FIN_QUEUE:
                break

            try:
                req = requests_reader(_sock)
                if not req:
                    continue
                method, uri = parse_request(req)

                if method.upper() == "GET":
                    do_get(uri, _sock)
                elif method.upper() == "HEAD":
                    do_head(uri, _sock)
                else:
                    logging.error(f"Wrong method: {method!r} in request {req!r}")
                    raise ErrorCode(HTTPStatus.METHOD_NOT_ALLOWED)
            except ErrorCode as e:
                send_response(_sock, None, e.err_code)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Error in {mp.current_process().name} is:\n{e!r}")
    finally:
        logging.info(f"Process {mp.current_process().name} stoped.")


###########################################################
#                      https server                       #
###########################################################


def main_loop(config):
    try:
        queue = mp.Queue()
        processes = set()

        for i in range(config.workers):
            p = mp.Process(target=worker, args=(queue,))
            processes.add(p)
            p.start()

        logging.info(f"Created process pool with {config.workers} workers.")

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((config.address, config.port))
        serversocket.listen(config.workers)

        logging.info(
            f"Created server at address {config.address} and port {config.port}"
        )

        while True:
            connectiontoclient, address = serversocket.accept()
            connectiontoclient.settimeout(settings.cfg["SOCKS_TIMEOUT"])
            queue.put(connectiontoclient)
    except KeyboardInterrupt:
        pass
    finally:
        logging.debug("Closing processes..")
        for _ in processes:
            queue.put(FIN_QUEUE)
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
    cfg_folder = os.path.join(pwd, args.folder.lstrip("/"))

    if not os.path.isdir(cfg_folder):
        logging.error(f"Folder: {cfg_folder} doesn't exist")
        res = False

    if args.workers < 1:
        logging.error(
            f"Number of workers can not be less than 1, now {args.workers}"
        )
        res = False

    return res


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname).1s] %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        stream=sys.stdout,
    )

    ap = argparse.ArgumentParser()
    ap.add_argument("-a", "--address", action="store", default="127.0.0.1")
    ap.add_argument("-p", "--port", action="store", type=int, default=8080)
    ap.add_argument("-r", "--folder", action="store", default="/httptest")
    ap.add_argument("-w", "--workers", action="store", type=int, default=8)
    args = ap.parse_args()

    if check_args(args):
        try:
            main_loop(args)
        except Exception as e:
            logging.exception(f"{e!r}")
