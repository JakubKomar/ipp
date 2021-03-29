#!/usr/bin/env python3

#autor: Jakub Komarek
#login: xkomar33
#ipp- interperet kodu v xml
import sys
import os
import re

def stringConverter(old):
    new=bytes(old,encoding="utf-8")
    regex = re.compile(rb"\\(\d{1,3})")
    def replace(match):
        return int(match.group(1)).to_bytes(1, byteorder="big")
    new = regex.sub(replace, new)
    new= new.decode("utf-8")
    return new
line=str("hello\\035word")
line=stringConverter(line)
print(line)
