# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Nico Schlömer
#
# This file is part of matplotlib2tikz.
#
# matplotlib2tikz is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# matplotlib2tikz is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# matplotlib2tikz.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import tempfile
from importlib import import_module
import hashlib
import subprocess
#import wand.image
#import poppler
from PIL import Image
import imagehash

import matplotlib2tikz
import testfunctions


def test_generator():
    for name in testfunctions.__all__:
        print(name)
        test = import_module('testfunctions.' + name)
        yield check_hash, test


def check_hash(test):
    # import the test
    test.plot()
    # convert to tikz file
    handle, tikzfile = tempfile.mkstemp(suffix='_tikz.tex')
    matplotlib2tikz.save(
        tikzfile,
        figurewidth='7.5cm',
        show_info=False
        )
    # create a latex wrapper for the tikz
    wrapper = '''\\documentclass{standalone}
\\usepackage{pgfplots}
\\usepgfplotslibrary{groupplots}
\\pgfplotsset{compat=newest}
\\begin{document}
\\input{%s}
\\end{document}''' % tikzfile
    handle, tex_file = tempfile.mkstemp()
    with open(tex_file, 'w') as f:
        f.write(wrapper)

    # change into the directory of the TeX file
    os.chdir(os.path.dirname(tex_file))

    # compile the output to pdf
    FNULL = open(os.devnull, 'w')
    subprocess.check_call(
        # use pdflatex for now until travis features a more modern lualatex
        ['pdflatex', '--interaction=nonstopmode', tex_file],
        stdout=FNULL,
        stderr=subprocess.STDOUT
        )
    pdf_file = tex_file + '.pdf'

    # Convert PDF to PNG.
    base = tex_file
    png_file = tex_file + '-1.png'
    print(png_file)
    subprocess.check_call(
        ['pdftoppm', '-rx', '600', '-ry','600', '-png', pdf_file, base],
        stdout=FNULL,
        stderr=subprocess.STDOUT
        )

    # compute the phash of the PNG
    phash = imagehash.phash(Image.open(png_file)).__str__()
    print(phash)

    # Compute the Hamming distance between the two 64-bit numbers
    hamming_dist = bin(int(phash, 16) ^ int(test.phash, 16)).count('1')
    print(hamming_dist)

    assert test.phash == phash
