"""This module provides functionality for decoding the LZW format.

Binary12BitInput provides a wrapper over reading large files and converting them to 12-bit format
required by the LZW decoder.

LZW provides the means to decode an iterable of 12-bit LZW codewords.

CodewordTable is the symbol table used to store a mapping of LZW codewords to strings.

"""

import os
import io
import collections


class Binary12BitInput:
    """Provides an interface to the lzw file."""

    def __init__(self, filename: str):
        self._filename = filename

        nbits = os.stat(self._filename).st_size * 8
        self.file = open(self._filename, "rb")
        self.buffer = collections.deque()

        self.has_16bit_element = nbits % 12 != 0 and nbits >= 16
        self.n_12bits = nbits // 12

        self.i = 0
        self.n = 1
        self.previous_byte = 0
        self._finished = False

        # current bytes to translate into a 12-bit codeword
        self.current_bytes = [x
                              for x in self.file.read(2)]

    def __iter__(self):
        return self

    def _get_next_byte(self):
        """Return the next byte from the internal buffer."""
        if not self.buffer:
            self.buffer = collections.deque(self.file.read(io.DEFAULT_BUFFER_SIZE))

        return self.buffer.popleft()

    def __next__(self):
        """Get the next available codeword from the file."""
        if self._finished:
            self.file.close()
            raise StopIteration

        c12bit_codeword = 0
        if self.n < self.n_12bits:

            if self.n & 1 == 1:
                # From 0xAB 0xC? ..
                # Move 0xAB up by 4 to make space for C.
                top_4bits = self.current_bytes[0] << 4
                lower_8bits = (self.current_bytes[1] & 0xF0) >> 4

                c12bit_codeword = top_4bits | lower_8bits

                self.current_bytes[0] = self.current_bytes[1]
                self.current_bytes[1] = self._get_next_byte()

            else:
                # From 0x?A 0xBC
                # Move A into the top 4 bits and pad
                # in 0xBC in the bottom 8 bits.
                top_4bits = (self.current_bytes[0] & 0x0F) << 8
                lower_8bits = self.current_bytes[1]
                c12bit_codeword = top_4bits | lower_8bits

                self.current_bytes = [self._get_next_byte(), self._get_next_byte()]

            self.n += 1

        elif self.has_16bit_element:
            # The last 12-bit can be padded to 16-bits make the last element byte aligned.
            c12bit_codeword = self.current_bytes[0] << 8 | self.current_bytes[1]
            self._finished = True

        else:
            self._finished = True

        return c12bit_codeword


class CodewordTable:
    """Table which maps codewords to strings.
    """
    def __init__(self, size: int):
        self._size = size
        self._table = []
        self._reset()

    def _reset(self):
        self._table = [chr(x)
                       for x in range(256)]

    def put(self, string: str):
        if len(self._table) >= self._size:
            self._reset()

        self._table.append(string)

    def get(self, codeword: int) -> str:
        return self._table[codeword]


class LZW:

    def __init__(self, codewords, table_size=4096):
        """:param codewords : An iterable containing the codewords to decode.
           :param table_size : Size of the symbol table.
        """
        self._codewords = iter(codewords)
        self._table_size = table_size

    def expand(self):
        """Generator which yields a single decoded string at a time.
        """
        table = CodewordTable(self._table_size)

        cw0 = next(self._codewords)
        string = table.get(cw0)
        yield string

        for cw1 in self._codewords:
            try:
                ch1 = table.get(cw1)
                table_entry = string + ch1[0]
                table.put(table_entry)

                string = ch1

            except IndexError:
                table_entry = string + string[0]
                table.put(table_entry)

                string = table_entry

            yield string


if __name__ == '__main__':
    """Run an example provided from the command line."""
    import sys
    try:
        name = sys.argv[1]
        lzw = LZW(Binary12BitInput(name))

        for c in lzw.expand():
            print(c, end="")

    except IndexError:
        print("Please provide an LZW filename as the first argument.")
