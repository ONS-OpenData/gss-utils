class BytesIOWrapper:
    def __init__(self, string_buffer, encoding='utf-8'):
        self.string_buffer = string_buffer
        self.encoding = encoding

    def __getattr__(self, attr):
        return getattr(self.string_buffer, attr)

    def read(self, size=-1):
        content = self.string_buffer.read(size)
        return content.encode(self.encoding)

    def write(self, b):
        content = b.decode(self.encoding)
        return self.string_buffer.write(content)
