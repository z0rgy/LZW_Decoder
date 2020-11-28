from unittest import TestCase
from lzw import LZW, Binary12BitInput
import pathlib
import os
import io


def to_string(lz: LZW):
    """Helper function used to expand a LZW into a string"""
    sio = io.StringIO()
    for c in lz.expand():
        sio.write(c)

    return sio.getvalue()


class LZWTest(TestCase):

    def test_lzw_single(self):
        """LZWTest the basic simple case where each codeword is a single character
        and there are no strings.
        """
        lzw = LZW([0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A,
                   0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50])

        self.assertEqual("ABCDEFGHIJKLMNOP", to_string(lzw))

    def test_lzw_mixed_case0(self):
        """LZWTest a codewords which represent both characters and strings."""
        lzw = LZW([0x41, 0x42, 0x43, 0x44, 0x100, 0x104,
                   0x101, 0x44, 0x101, 0x5A, 0x5A])

        self.assertEqual("ABCDABABABCDBCZZ", to_string(lzw))

    def test_lzw_mixed_case1(self):
        """LZWTest a codewords which represent both characters and strings."""
        lzw = LZW([0x41, 0x42, 0x100, 0x43, 0x102, 0x102, 0x44, 0x45])

        self.assertEqual("ABABCABCABCDE", to_string(lzw))

    def test_lzw_alternate_pattern(self):
        """LZWTest alternating pattern between char and string starting with a double char
        and ending with a char."""
        lzw = LZW([0x41, 0x42, 0x100, 0x43, 0x102, 0x44, 0x104, 0x45])

        self.assertEqual("ABABCABCDABCDE", to_string(lzw))

    def test_lzw_char_string(self):
        """LZWTest the pattern of a single character followed by a string consisting
        of that character.
        """
        lzw = LZW([0x41, 0x100, 0x42, 0x102, 0x43, 0x104, 0x44, 0x106, 0x45, 0x108])

        self.assertEqual("AAABBBCCCDDDEEE", to_string(lzw))

    def test_lzw_growing(self):
        """LZWTest consecutive cases of the corner case.
        The corner case is: Whilst decoding, the codeword in the dictionary does not exist.

        This is when the current codeword for instance 'A' is the next codeword 'AA'.
        """
        lzw = LZW([0x41, 0x100, 0x101, 0x102, 0x103])

        self.assertEqual("AAAAAAAAAAAAAAA", to_string(lzw))

    def test_lzw_reset(self):
        """LZWTest whether or not resetting the table works as expected.

        The expected behaviour is that strings put in the string table
        will not be used. This is due to the table being reset.
        """
        lzw = LZW([0x41, 0x42, 0x43, 0x41, 0x42, 0x43, 0x41,
                   0x44, 0x41, 0x43, 0x42, 0x45, 0x44, 0x41],
                  table_size=258)

        self.assertEqual("ABCABCADACBEDA", to_string(lzw))

    def test_lzw_reset0(self):
        """LZWTest whether or not resetting the table works as expected.

        The expected behaviour is that strings put in the string table
        will not be used. This is due to the table being reset.
        """
        lzw = LZW([0x41, 0x42, 0x43, 0x100, 0x102,
                   0x42, 0x43, 0x41, 0x42, 0x43, 0x41, 0x100],
                  table_size=260)

        self.assertEqual("ABCABCABCABCABC", to_string(lzw))


class BinaryInputTest(TestCase):

    def test_binary_input(self):
        filename = r"examples/compressedfile4.z"
        bs = pathlib.Path(filename).read_bytes()
        nbits = os.stat(filename).st_size * 8
        has_last = nbits % 12 != 0

        codewords = []
        i = 0
        n = 1
        n_12bits = nbits // 12
        while n < n_12bits:
            if n % 2 != 0:
                codewords.append(bs[i] << 4 | (bs[i + 1] & 0xF0) >> 4)
                i += 1
            else:
                codewords.append((bs[i] & 0x0F) << 8 | bs[i + 1])
                i += 2
            n += 1

        if has_last:
            codewords.append(bs[i] << 8 | bs[i + 1])

        bi = Binary12BitInput(filename)
        codewords2 = [x for x in bi]
        self.assertEqual(codewords, codewords2)

