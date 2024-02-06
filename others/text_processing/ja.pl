#!/usr/bin/perl -p

s/(?<!。)\n//g;    # remove newlines if not after 。
s/。(?!\n)/。\n/g;  # add newlines after 。 if needed

# (Linux) Create two files i.txt and o.txt
# copy paste the text in i.txt then run:
# ./ja.pl < i.txt > o.txt
# the result will be in o.txt

# Also with xclip
# xclip -o | ./ja.pl | xclip -selection clipboard
# (may need chmod +x ja.pl)