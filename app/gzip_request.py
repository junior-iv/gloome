import io
import zlib

MAX_DECOMPRESSED_BODY_SIZE = 1024 ** 3  # 1 GiB; guards against gzip bombs
CHUNK_SIZE = 1024 * 1024


class GzipRequestMiddleware:
    """Decompresses request bodies sent with 'Content-Encoding: gzip'.

    The front end gzips large form posts so they fit under the reverse proxy's body-size limit
    (nginx defaults to 1 MB). The proxy only sees the compressed size; after this middleware Flask
    sees an ordinary form, so request.form works unchanged in every route.
    """

    def __init__(self, wsgi_app, max_size: int = MAX_DECOMPRESSED_BODY_SIZE):
        self.wsgi_app = wsgi_app
        self.max_size = max_size

    def __call__(self, environ, start_response):
        if environ.get('HTTP_CONTENT_ENCODING', '').strip().lower() != 'gzip':
            return self.wsgi_app(environ, start_response)

        try:
            body = self.decompress(environ['wsgi.input'])
        except (zlib.error, ValueError) as e:
            message = f'Could not read the compressed request: {e}'.encode('utf-8')
            start_response('400 Bad Request', [('Content-Type', 'text/plain; charset=utf-8'),
                                               ('Content-Length', str(len(message)))])
            return [message]

        environ['wsgi.input'] = io.BytesIO(body)
        environ['CONTENT_LENGTH'] = str(len(body))
        del environ['HTTP_CONTENT_ENCODING']
        return self.wsgi_app(environ, start_response)

    def decompress(self, stream) -> bytes:
        decompressor = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)  # gzip container
        output = bytearray()
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            output += decompressor.decompress(chunk, self.max_size + 1 - len(output))
            if len(output) > self.max_size or decompressor.unconsumed_tail:
                raise ValueError(f'the request is larger than {self.max_size:,} bytes after decompression')
        output += decompressor.flush()
        if not decompressor.eof:
            raise ValueError('the compressed data is truncated')
        if len(output) > self.max_size:
            raise ValueError(f'the request is larger than {self.max_size:,} bytes after decompression')
        return bytes(output)
