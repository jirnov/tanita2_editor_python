LettersHeight = 22

LettersWidth = [100] * 256
LettersWidth[ord(' ')] = 12
LettersWidth[ord(':')] = 8
LettersWidth[ord('-')] = 6

LettersWidth[ord('!')] = 12
LettersWidth[ord('`')] = 12
LettersWidth[ord('\'')] = 9

LettersWidth[ord(',')] = 1
LettersWidth[ord('.')] = 2
LettersWidth[ord('0'):ord('9')+1] = [18, 10, 13, 13, 13, 14, 14, 11, 11, 15]
LettersWidth[ord('¸')] = LettersWidth[ord('¨')] = 16
LettersWidth[ord('à'):ord('ÿ')+1] = LettersWidth[ord('À'):ord('ß')+1] = \
    [14, 13, 14, 14, 19, 15, 18, 14, 15, 14, 14, 17,
     18, 13, 15, 15, 13, 15, 16, 13, 21, 15, 15, 15,
     19, 20, 22, 21, 14, 14, 19, 14]
LettersWidth[ord('U')] = 20
LettersWidth[149] = 2
