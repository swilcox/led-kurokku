"""
14-segment character mapping for HT16K33 displays.

Segment layout for 14-segment displays:
       A
   F  H I J  B
     G1  G2
   E  M L K  C
       D

Standard bit mapping (16-bit value):
  Bit 0: A (top horizontal)
  Bit 1: B (top right vertical)
  Bit 2: C (bottom right vertical)
  Bit 3: D (bottom horizontal)
  Bit 4: E (bottom left vertical)
  Bit 5: F (top left vertical)
  Bit 6: G1 (middle left horizontal)
  Bit 7: G2 (middle right horizontal)
  Bit 8: H (top left diagonal)
  Bit 9: I (top center vertical)
  Bit 10: J (top right diagonal)
  Bit 11: K (bottom right diagonal)
  Bit 12: L (bottom center vertical)
  Bit 13: M (bottom left diagonal)
  Bit 14: Decimal point (DP)
  Bit 15: Reserved/unused

This provides full alphanumeric character support.
"""

# 14-segment character mapping
# Each character maps to a 16-bit value representing which segments are lit
SEGMENTS_14 = {
    # Numbers 0-9
    "0": 0x003F,  # A1+A2+B+C+D1+D2+E+F
    "1": 0x0006,  # B+C
    "2": 0x00DB,  # A1+A2+B+G1+G2+E+D1+D2
    "3": 0x00CF,  # A+B+C+D+G1+G2
    "4": 0x00E6,  # F+G1+G2+B+C
    "5": 0x00ED,  # A1+A2+F+G1+G2+C+D1+D2
    "6": 0x00FD,  # A1+A2+F+G1+G2+E+C+D1+D2
    "7": 0x0007,  # A1+A2+B+C
    "8": 0x00FF,  # All standard segments
    "9": 0x00EF,  # A1+A2+F+G1+G2+B+C+D1+D2

    # Uppercase alphabet (full 14-segment capability)
    "A": 0x00F7,  # A1+A2+F+G1+G2+B+C+E
    "B": 0x128F,  # A1+A2+B+C+D1+D2+G2+I+L
    "C": 0x0039,  # A1+A2+F+E+D1+D2
    "D": 0x120F,  # A1+A2+B+C+D1+D2+I+L
    "E": 0x00F9,  # A1+A2+F+G1+G2+E+D1+D2
    "F": 0x00F1,  # A1+A2+F+G1+G2+E
    "G": 0x00BD,  # A1+A2+F+E+D1+D2+C+G2
    "H": 0x00F6,  # F+G1+G2+B+C+E
    "I": 0x1209,  # A1+A2+D1+D2+I+L
    "J": 0x001E,  # B+C+D1+D2+E
    "K": 0x2470,  # F+G1+E+H+K
    "L": 0x0038,  # F+E+D1+D2
    "M": 0x0536,  # F+B+C+E+H+J
    "N": 0x2136,  # F+B+C+E+H+M
    "O": 0x003F,  # A1+A2+B+C+D1+D2+E+F
    "P": 0x00F3,  # A1+A2+F+G1+G2+B+E
    "Q": 0x203F,  # A1+A2+B+C+D1+D2+E+F+M
    "R": 0x20F3,  # A1+A2+F+G1+G2+B+E+M
    "S": 0x00ED,  # A1+A2+F+G1+G2+C+D1+D2
    "T": 0x1201,  # A1+A2+I+L
    "U": 0x003E,  # F+B+C+D1+D2+E
    "V": 0x4430,  # F+E+H+K
    "W": 0x2836,  # F+B+C+E+K+M
    "X": 0x4D00,  # H+J+K+M (diagonals)
    "Y": 0x1500,  # H+J+L
    "Z": 0x4409,  # A1+A2+D1+D2+H+K

    # Lowercase alphabet (selected characters that display well)
    "a": 0x00F7,  # Same as uppercase (some displays)
    "b": 0x00FC,  # F+G1+G2+E+C+D1+D2
    "c": 0x00D8,  # G1+G2+E+D1+D2
    "d": 0x00DE,  # B+G1+G2+C+D1+D2+E
    "e": 0x00F9,  # Same as uppercase
    "f": 0x00F1,  # Same as uppercase
    "g": 0x00EF,  # A1+A2+F+G1+G2+B+C+D1+D2
    "h": 0x00F4,  # F+G1+G2+C+E
    "i": 0x1000,  # L (center vertical)
    "j": 0x000E,  # B+C+D1+D2
    "k": 0x2470,  # Same as uppercase
    "l": 0x1200,  # I+L
    "m": 0x10D4,  # G1+G2+C+E+L
    "n": 0x10D0,  # G1+G2+C+E+L
    "o": 0x00DC,  # G1+G2+E+C+D1+D2
    "p": 0x00F3,  # Same as uppercase
    "q": 0x00E7,  # A1+A2+F+G1+G2+B+C
    "r": 0x00D0,  # G1+G2+E
    "s": 0x00ED,  # Same as uppercase
    "t": 0x00F8,  # F+G1+G2+E+D1+D2
    "u": 0x001C,  # B+C+D1+D2
    "v": 0x4010,  # E+K
    "w": 0x2814,  # C+D1+K+M
    "x": 0x4D00,  # Same as uppercase
    "y": 0x008E,  # B+C+G1+G2+D1+D2
    "z": 0x4409,  # Same as uppercase

    # Special characters
    " ": 0x0000,  # Space (all segments off)
    "-": 0x00C0,  # G1+G2 (minus sign)
    "_": 0x0008,  # D1 (underscore)
    "*": 0x2DC0,  # Degree symbol / asterisk (H+J+K+M diagonals + G1+G2 horizontals, bits 6,7,8,10,11,13)
    ".": 0x8000,  # Decimal point (bit 15, if supported by hardware)
    ",": 0x8000,  # Comma (same as decimal point)
    "!": 0x1206,  # B+C+I+L (exclamation)
    "?": 0x1083,  # A1+A2+B+G2+I (question mark)
    "/": 0x4400,  # H+K (forward slash)
    "\\": 0x2100, # J+M (backslash)
    "+": 0x1EC0,  # G1+G2+I+J+K+L (plus sign)
    "=": 0x00C8,  # G1+G2+D1+D2 (equals)
    "'": 0x0200,  # J (apostrophe)
    '"': 0x0500,  # H+J (quotation marks)
    "(": 0x4900,  # H+K (left paren)
    ")": 0x2400,  # J+M (right paren)
    "[": 0x0039,  # A1+A2+F+E+D1+D2 (left bracket)
    "]": 0x000F,  # A1+A2+B+C+D1+D2 (right bracket)
    "<": 0x4100,  # H+M (less than)
    ">": 0x2400,  # J+K (greater than)
    ":": 0x1200,  # I+L (colon)
    ";": 0x9200,  # I+L+decimal (semicolon)
    "^": 0x0403,  # A1+A2+H (caret)
    "&": 0x6359,  # Complex ampersand approximation
    "#": 0x12CE,  # Hash/pound sign
    "@": 0x12BB,  # At sign approximation
    "%": 0x6C24,  # Percent sign approximation
    "$": 0x12ED,  # Dollar sign (S with center vertical)
}

# Reverse lookup for debugging (segment value -> character)
REVERSE_SEGMENTS_14 = {v: k for k, v in SEGMENTS_14.items()}
