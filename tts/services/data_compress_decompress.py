import zlib


class Compress_Decompress:
    def __init__(self):
        self.compression_level = 9

    def compress_data(self, data):
        if self.compression_level < 0 or self.compression_level > 9:
            return "Enter valid compression level,zlib has 10 compression levels (0-9), a lower the number means lower latency for compression and deflation at the cost of a less-compressed file, while a higher number favors better compression at the cost of higher latency"
        if type(data) != bytes:
            data = data.encode()
        return zlib.compress(data, self.compression_level)

    def decompress_data(self, data):
        return zlib.decompress(data)
