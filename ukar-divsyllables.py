#!/usr/bin/python3
# Experimental syllable divider for Russian and Bulgarian languages
# TODO: Correctly handle prefixes

import sys

if len(sys.argv) < 2 or len(sys.argv) > 3:
    sys.stderr.write("Usage: mykar-divsyllables lang infile.txt > outfile.syl\n")
    sys.stderr.write("Supported languages: ru, bg\n")
    sys.exit(1)

lang = sys.argv[1]

if lang == "ru":
    vowels = set("аоуыэяёюие")
    cosons = set("йцкнгшщзхфвпрлджчсмитб")
    signs = set("ьъ")
elif lang == "bg":
    vowels = set("аоуъяюие")
    cosons = set("йцкнгшщзхфвпрлджчсмитб")
    signs = set("ь")
else:
    sys.stderr.write("Unupported language: %s\n" % lang)
    sys.exit(1)

letters = vowels | cosons | signs

if len(sys.argv) == 2:
   f = sys.stdin
else:
   f = open(sys.argv[2],"r", encoding = "utf-8")

for line in f:
   x = 0
   newline = ""
   while x < len(line):
       if line[x] in "-\\":
           newline += "\\" + line[x]
           x += 1
           continue
       elif x > 0 and line[x] == " " and line[x-1].lower() in letters:
           for x2 in range(x+1, len(line)):
               if line[x2] in letters:
                   newline += "-"
                   break
       newline += line[x]
       def get(x):
           if x < 0 or x >= len(line): return " "
           return line[x].lower()
       if get(x) in vowels:
           if get(x+1) in vowels: # or get(x-1) not in letters:
               newline += "-"
           elif get(x+1) in cosons:
               if get(x+2) in vowels:
                   newline += "-"
               elif get(x+2) == "ь" and get(x+3) == "о":
                   newline += "-"
       elif x > 0 and ((get(x) in cosons and newline[-2].lower() in vowels and get(x+1) not in signs) or (get(x) in signs and get(x-2) in vowels)):
           for x2 in range(x+1, len(line)):
               if get(x2) in vowels:
                   newline += "-"
                   break
               elif get(x2) not in letters:
                   break
       x += 1
   sys.stdout.write(newline)
   sys.stdout.flush()
