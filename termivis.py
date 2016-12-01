#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import fcntl
import struct
import termios
import argparse
import itertools

from PIL import Image
from PIL.ImagePalette import ImagePalette

PALETTES = {
    'tango': (
        (0x00, 0x00, 0x00), (0xcc, 0x00, 0x00),
        (0x4e, 0x9a, 0x06), (0xc4, 0xa0, 0x00),
        (0x34, 0x65, 0xa4), (0x75, 0x50, 0x7b),
        (0x06, 0x98, 0x9a), (0xd3, 0xd7, 0xcf),
        (0x55, 0x57, 0x53), (0xef, 0x29, 0x29),
        (0x8a, 0xe2, 0x34), (0xfc, 0xe9, 0x4f),
        (0x72, 0x9f, 0xcf), (0xad, 0x7f, 0xa8),
        (0x34, 0xe2, 0xe2), (0xee, 0xee, 0xec)
    ),
    'linux': (
        (0x00, 0x00, 0x00), (0xaa, 0x00, 0x00),
        (0x00, 0xaa, 0x00), (0xaa, 0x55, 0x00),
        (0x00, 0x00, 0xaa), (0xaa, 0x00, 0xaa),
        (0x00, 0xaa, 0xaa), (0xaa, 0xaa, 0xaa),
        (0x55, 0x55, 0x55), (0xff, 0x55, 0x55),
        (0x55, 0xff, 0x55), (0xff, 0xff, 0x55),
        (0x55, 0x55, 0xff), (0xff, 0x55, 0xff),
        (0x55, 0xff, 0xff), (0xff, 0xff, 0xff)
    ),
    'xterm': (
        (0x00, 0x00, 0x00), (0xcd, 0x00, 0x00),
        (0x00, 0xcd, 0x00), (0xcd, 0xcd, 0x00),
        (0x00, 0x00, 0xee), (0xcd, 0x00, 0xcd),
        (0x00, 0xcd, 0xcd), (0xe5, 0xe5, 0xe5),
        (0x7f, 0x7f, 0x7f), (0xff, 0x00, 0x00),
        (0x00, 0xff, 0x00), (0xff, 0xff, 0x00),
        (0x5c, 0x5c, 0xff), (0xff, 0x00, 0xff),
        (0x00, 0xff, 0xff), (0xff, 0xff, 0xff)
    ),
    'rxvt': (
        (0x00, 0x00, 0x00), (0xcd, 0x00, 0x00),
        (0x00, 0xcd, 0x00), (0xcd, 0xcd, 0x00),
        (0x00, 0x00, 0xcd), (0xcd, 0x00, 0xcd),
        (0x00, 0xcd, 0xcd), (0xfa, 0xeb, 0xd7),
        (0x40, 0x40, 0x40), (0xff, 0x00, 0x00),
        (0x00, 0xff, 0x00), (0xff, 0xff, 0x00),
        (0x00, 0x00, 0xff), (0xff, 0x00, 0xff),
        (0x00, 0xff, 0xff), (0xff, 0xff, 0xff)
    ),
    'solarized': (
        (0x07, 0x36, 0x42), (0xdc, 0x32, 0x2f),
        (0x85, 0x99, 0x00), (0xb5, 0x89, 0x00),
        (0x26, 0x8b, 0xd2), (0xd3, 0x36, 0x82),
        (0x2a, 0xa1, 0x98), (0xee, 0xe8, 0xd5),
        (0x00, 0x2b, 0x36), (0xcb, 0x4b, 0x16),
        (0x58, 0x6e, 0x75), (0x65, 0x7b, 0x83),
        (0x83, 0x94, 0x96), (0x6c, 0x71, 0xc4),
        (0x93, 0xa1, 0xa1), (0xfd, 0xf6, 0xe3)
    )
}
ANSI_256 = tuple(tuple(int(x[y*2:(y+1)*2], 16) for y in range(3)) for x in (
    '000000,00005f,000087,0000af,0000d7,0000ff,005f00,005f5f,'
    '005f87,005faf,005fd7,005fff,008700,00875f,008787,0087af,'
    '0087d7,0087ff,00af00,00af5f,00af87,00afaf,00afd7,00afff,'
    '00d700,00d75f,00d787,00d7af,00d7d7,00d7ff,00ff00,00ff5f,'
    '00ff87,00ffaf,00ffd7,00ffff,5f0000,5f005f,5f0087,5f00af,'
    '5f00d7,5f00ff,5f5f00,5f5f5f,5f5f87,5f5faf,5f5fd7,5f5fff,'
    '5f8700,5f875f,5f8787,5f87af,5f87d7,5f87ff,5faf00,5faf5f,'
    '5faf87,5fafaf,5fafd7,5fafff,5fd700,5fd75f,5fd787,5fd7af,'
    '5fd7d7,5fd7ff,5fff00,5fff5f,5fff87,5fffaf,5fffd7,5fffff,'
    '870000,87005f,870087,8700af,8700d7,8700ff,875f00,875f5f,'
    '875f87,875faf,875fd7,875fff,878700,87875f,878787,8787af,'
    '8787d7,8787ff,87af00,87af5f,87af87,87afaf,87afd7,87afff,'
    '87d700,87d75f,87d787,87d7af,87d7d7,87d7ff,87ff00,87ff5f,'
    '87ff87,87ffaf,87ffd7,87ffff,af0000,af005f,af0087,af00af,'
    'af00d7,af00ff,af5f00,af5f5f,af5f87,af5faf,af5fd7,af5fff,'
    'af8700,af875f,af8787,af87af,af87d7,af87ff,afaf00,afaf5f,'
    'afaf87,afafaf,afafd7,afafff,afd700,afd75f,afd787,afd7af,'
    'afd7d7,afd7ff,afff00,afff5f,afff87,afffaf,afffd7,afffff,'
    'd70000,d7005f,d70087,d700af,d700d7,d700ff,d75f00,d75f5f,'
    'd75f87,d75faf,d75fd7,d75fff,d78700,d7875f,d78787,d787af,'
    'd787d7,d787ff,d7af00,d7af5f,d7af87,d7afaf,d7afd7,d7afff,'
    'd7d700,d7d75f,d7d787,d7d7af,d7d7d7,d7d7ff,d7ff00,d7ff5f,'
    'd7ff87,d7ffaf,d7ffd7,d7ffff,ff0000,ff005f,ff0087,ff00af,'
    'ff00d7,ff00ff,ff5f00,ff5f5f,ff5f87,ff5faf,ff5fd7,ff5fff,'
    'ff8700,ff875f,ff8787,ff87af,ff87d7,ff87ff,ffaf00,ffaf5f,'
    'ffaf87,ffafaf,ffafd7,ffafff,ffd700,ffd75f,ffd787,ffd7af,'
    'ffd7d7,ffd7ff,ffff00,ffff5f,ffff87,ffffaf,ffffd7,ffffff,'
    '080808,121212,1c1c1c,262626,303030,3a3a3a,444444,4e4e4e,'
    '585858,626262,6c6c6c,767676,808080,8a8a8a,949494,9e9e9e,'
    'a8a8a8,b2b2b2,bcbcbc,c6c6c6,d0d0d0,dadada,e4e4e4,eeeeee'
).split(','))

def _getdimensions():
    call = fcntl.ioctl(1, termios.TIOCGWINSZ, "\000"*8)
    height, width = struct.unpack("hhhh", call)[:2]
    return width, height

def get_terminal_dimensions():
    # Copied from PyPy.
    try:
        width, height = _getdimensions()
    except (KeyboardInterrupt, SystemExit, MemoryError, GeneratorExit):
        raise
    except:
        # FALLBACK
        width = int(os.environ.get('COLUMNS', 80))
        height = int(os.environ.get('LINES', 80))
    else:
        # XXX the windows getdimensions may be bogus, let's sanify a bit
        if width < 40:
            width = 80
            height = 24
    return width, height

class Image2ANSI:
    DEFAULT_PALETTE = 'tango'

    def __init__(self, mode, palette=None):
        if mode == '4b':
            self.colors = 16
            self.pal = Image.new('P', (4, 4))
            self.pal.putpalette(
                tuple(itertools.chain.from_iterable(
                PALETTES[palette or DEFAULT_PALETTE])) * 16
            )
            self.pal.load()
            self.func_fg = lambda x: '\x1b[%d%dm' % (9 if x//8 else 3, x%8)
            self.func_bg = lambda x: '\x1b[%d%dm' % (10 if x//8 else 4, x%8)
        elif mode == '8b':
            self.colors = 256
            self.pal = Image.new('P', (16, 16))
            self.pal.putpalette(
                tuple(itertools.chain.from_iterable(
                PALETTES[palette or DEFAULT_PALETTE] + ANSI_256))
            )
            self.pal.load()
            self.func_fg = lambda x: '\x1b[38;5;%dm' % x
            self.func_bg = lambda x: '\x1b[48;5;%dm' % x
        else:
            # 24bit
            self.colors = None
            self.pal = None
            self.func_fg = lambda x: '\x1b[38;2;%d;%d;%dm' % x
            self.func_bg = lambda x: '\x1b[48;2;%d;%d;%dm' % x

    def convert(self, img, width, height):
        newimg = img.convert('RGB').resize((width, height), Image.LANCZOS)
        if self.pal:
            im = newimg.im.convert('P', 1, self.pal.im)
            newimg = newimg._makeself(im)
        padding = height % 2
        lastfg = lastbg = None
        yield '\x1b[?25l\x1b[2J\x1b[1H'
        for y in range(0, height, 2):
            if padding and y == height-1:
                yield '\x1b[49m'
            for x in range(width):
                fg = newimg.getpixel((x, y))
                if lastfg != fg or self.colors == 16:
                    yield self.func_fg(fg)
                    lastfg = fg
                if not padding or y != height-1:
                    bg = newimg.getpixel((x, y+1))
                    if lastbg != bg:
                        yield self.func_bg(bg)
                        lastbg = bg
                yield '▀'
            yield '\n'
        yield '\x1b[0;39;49m'
        yield '\x1b[?25h'

def paint(filename, mode='24b', palette='tango', width=None, height=None):
    ia = Image2ANSI(mode, palette)
    img = Image.open(filename)
    if width and not height:
        width = int(width)
        height = int(width / img.width * img.height)
    elif height and not width:
        height = int(height)
        width = int(height / img.height * img.width)
    else:
        width, height = get_terminal_dimensions()
        height *= 2
        neww = int(height / img.height * img.width)
        newh = int(width / img.width * img.height)
        if neww > width:
            height = newh
        elif newh > height:
            width = neww
    for s in ia.convert(img, width, height):
        sys.stdout.write(s)
    sys.stdout.flush()

if __name__ == '__main__':
    sys.exit(paint(*sys.argv[1:]))
