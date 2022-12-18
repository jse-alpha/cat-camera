# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

__version__ = "v1.0"

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
from pathlib import Path
from string import Template


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = load_html_template().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def _html_str_replace(
    html: str,
    mapped: dict = {
        r'\r': '.',
        r'\n': ' ',
        '>NaT<': '><'
    }
) -> str:

    ''' Replace characters in html based on mapped dict. '''

    for chars in mapped:
        html = html.replace(chars, mapped[chars])

    return html


def load_html_template(
    html_template_path: Path = Path("template/camera_page_template.html")
) -> str:

    ''' Load HTML template string. '''

    with open(
        html_template_path
    ) as template_file:

        template = Template(template_file.read())

    params = {
        'cam_version': __version__
    }

    html = template.substitute(params)

    # Remove NaT (not a time)
    return _html_str_replace(html)


if __name__=="__main__":

    with picamera.PiCamera(resolution='1536x1152', framerate=24) as camera:
        output = StreamingOutput()

        camera.rotation = 180
        camera.start_recording(output, format='mjpeg')

        try:
            address = ('', 8081)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()

        finally:
            camera.stop_recording()
