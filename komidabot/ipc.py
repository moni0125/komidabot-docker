import atexit
import json
import os
import socket
import struct
import sys
import threading
import traceback
from typing import Dict, Optional

from komidabot.debug.state import DebuggableException

SOCKET_PATH = '/tmp/komidabot_socket'


def start_server(callback):
    if callback is None:
        raise ValueError('callback is None')
    if not callable(callback):
        raise ValueError('callback is not callable')

    path = SOCKET_PATH
    running = True
    thread: Optional[threading.Thread] = None
    sock: Optional[socket.socket] = None

    client_threads: Dict[int, threading.Thread] = {}
    next_thread_id = 1

    def stop_server():
        nonlocal running

        running = False
        if sock is not None:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        if thread is not None:
            print('Waiting for server thread', flush=True)
            thread.join()
        os.unlink(path)

    if os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            if os.path.exists(path):
                raise

    def client_communication_thread(thread_id, connection: socket.socket):
        try:
            with connection:
                print('New client thread', thread_id, flush=True)

                while running:
                    data = connection.recv(4)
                    if len(data) < 4:
                        break
                    length, = struct.unpack('>I', data)

                    data = connection.recv(length)
                    msg = data.decode('utf-8')
                    obj = json.loads(msg)

                    callback(obj)

        except DebuggableException as e:
            print('Exception raised in client thread', thread_id, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print(e.get_trace(), file=sys.stderr, flush=True)
        except Exception:
            print('Exception raised in client thread', thread_id, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
        finally:
            print('Client thread stopped', thread_id, flush=True)

            if running:
                del client_threads[thread_id]

    def server_thread():
        nonlocal next_thread_id, running, sock

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.bind(path)
            sock.listen(1)

            while running:
                try:
                    connection, client_addr = sock.accept()
                except OSError:
                    continue

                thread_id = next_thread_id
                next_thread_id = next_thread_id + 1

                client_thread = threading.Thread(target=client_communication_thread,
                                                 args=(thread_id, connection),
                                                 name='IPC Reader Thread {}'.format(thread_id),
                                                 daemon=True)

                client_threads[thread_id] = client_thread
                client_thread.start()

        running = False
        print('Server thread stopping', flush=True)

        for thread_id, client_thread in client_threads.items():
            print('Waiting for client thread', thread_id, flush=True)
            client_thread.join()

    thread = threading.Thread(target=server_thread, name='IPC Server', daemon=True)
    thread.start()

    atexit.register(stop_server)


def send_message(obj):
    path = SOCKET_PATH

    if not os.path.exists(path):
        raise Exception('Server not listening')

    msg = json.dumps(obj)
    data = msg.encode('utf-8')

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(path)

        length_bytes = struct.pack('>I', len(data))

        sock.sendall(length_bytes)
        sock.sendall(data)
