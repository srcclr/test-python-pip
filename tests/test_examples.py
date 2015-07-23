# Copyright (c) 2015 Uber Technologies, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import contextlib
import os
import subprocess
import socket
import time

import pytest


@contextlib.contextmanager
def popen(path):
    process = subprocess.Popen(
        ['python', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process.poll()

    try:
        yield process
    finally:
        process.kill()


@pytest.yield_fixture
def examples_dir():
    cwd = os.getcwd()

    examples = os.path.join(cwd, 'examples')

    assert os.path.exists(examples)

    try:
        os.chdir(examples)
        yield examples
    finally:
        os.chdir(cwd)


def wait_until_connectable(port):
    count = 0
    while count < 50:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', port))
        except socket.error as e:
            count += 1
            time.sleep(0.01)
        else:
            sock.close()
            return

    raise Exception('Could not connect to server at port %d' % port)


@pytest.mark.parametrize(
    'example_type, port',
    [
        ('raw_', 8888),
        ('json_', 8888),
        ('thrift_examples/', 8888),
        ('keyvalue/keyvalue/', 8889),
        # 'stream_',
    ]
)
def test_example(examples_dir, example_type, port):
    """Smoke test example code to ensure it still runs."""

    server_path = os.path.join(
        examples_dir,
        example_type + 'server.py',
    )

    client_path = os.path.join(
        examples_dir,
        example_type + 'client.py',
    )

    with popen(server_path):
        wait_until_connectable(port)

        with popen(client_path) as client:
            assert (
                client.stdout.read() == 'Hello, world!\n'
            ), client.stderr.read()
