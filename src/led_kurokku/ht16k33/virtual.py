"""Virtual terminal driver for HT16K33 14-segment displays.

Renders 14-segment displays in the terminal using Unicode characters.
"""

import sys

from ..tm1637.base_driver import BaseDriver


class HT16K33VirtualDriver(BaseDriver):
    """
    Terminal-based virtual driver for HT16K33 14-segment displays.

    Renders 14-segment characters in the terminal using Unicode box-drawing characters.
    Provides visual feedback without requiring physical hardware.
    """

    def __init__(self):
        """Initialize the HT16K33 virtual driver."""
        super().__init__()
        self._driver_name = "HT16K33-virtual"
        self.current_display = [0, 0, 0, 0]
        self.display_height = 7  # 14-segment needs more height than 7-segment
        self.is_first_display = True

        # Unicode characters for rendering
        self.chars = {
            "h_bar": "━",  # Horizontal line
            "v_bar": "┃",  # Vertical line
            "diag_down": "╲",  # Diagonal down-right
            "diag_up": "╱",  # Diagonal up-right
            "space": " ",
            "colon": "∶",
        }

    def _render_14seg_digit(self, segment_bits: int) -> list[str]:
        """
        Render a single 14-segment digit to terminal lines.

        14-segment layout (simplified for terminal):
             A1  A2        (top horizontal, split)
           F  H I J  B     (upper section with diagonals)
             G1  G2        (middle horizontal, split)
           E  M L K  C     (lower section with diagonals)
             D1  D2        (bottom horizontal, split)

        Bit mapping (first 14 bits of 16-bit value):
        0-7:  A1 A2 B C D2 D1 E F
        8-15: G1 G2 H I J K L M (and decimal point)

        :param segment_bits: 16-bit value representing which segments are lit.
        :return: List of 7 strings representing the digit.
        """

        def has_bit(position: int) -> bool:
            return (segment_bits & (1 << position)) != 0

        # Segment positions in our bit layout
        # Standard mapping: A1=0, A2=1, B=2, C=3, D2=4, D1=5, E=6, F=7
        # G1=8, G2=9, H=10, I=11, J=12, K=13, L=14, M=15
        a1 = has_bit(0)
        a2 = has_bit(1)
        b = has_bit(2)
        c = has_bit(3)
        d2 = has_bit(4)
        d1 = has_bit(5)
        e = has_bit(6)
        f = has_bit(7)
        g1 = has_bit(8)
        g2 = has_bit(9)
        h = has_bit(10)
        i = has_bit(11)
        j = has_bit(12)
        k = has_bit(13)
        l = has_bit(14)
        m = has_bit(15)

        # Build 7-line display (increased from 5 for more detail)
        # Line 0: Top horizontal (A1, A2)
        line0_left = self.chars["h_bar"] * 2 if a1 else "  "
        line0_right = self.chars["h_bar"] * 2 if a2 else "  "
        line0 = f" {line0_left} {line0_right} "

        # Line 1: Upper section with diagonals (F, H, I, J, B)
        l1_f = self.chars["v_bar"] if f else " "
        l1_h = self.chars["diag_down"] if h else " "
        l1_i = self.chars["v_bar"] if i else " "
        l1_j = self.chars["diag_up"] if j else " "
        l1_b = self.chars["v_bar"] if b else " "
        line1 = f"{l1_f}{l1_h} {l1_i} {l1_j}{l1_b}"

        # Line 2: Upper-mid verticals (F, I, B)
        l2_f = self.chars["v_bar"] if f else " "
        l2_i = self.chars["v_bar"] if i else " "
        l2_b = self.chars["v_bar"] if b else " "
        line2 = f"{l2_f}   {l2_i}   {l2_b}"

        # Line 3: Middle horizontal (G1, G2)
        l3_g1 = self.chars["h_bar"] * 2 if g1 else "  "
        l3_g2 = self.chars["h_bar"] * 2 if g2 else "  "
        line3 = f" {l3_g1} {l3_g2} "

        # Line 4: Lower-mid verticals (E, L, C)
        l4_e = self.chars["v_bar"] if e else " "
        l4_l = self.chars["v_bar"] if l else " "
        l4_c = self.chars["v_bar"] if c else " "
        line4 = f"{l4_e}   {l4_l}   {l4_c}"

        # Line 5: Lower section with diagonals (E, M, L, K, C)
        l5_e = self.chars["v_bar"] if e else " "
        l5_m = self.chars["diag_up"] if m else " "
        l5_l = self.chars["v_bar"] if l else " "
        l5_k = self.chars["diag_down"] if k else " "
        l5_c = self.chars["v_bar"] if c else " "
        line5 = f"{l5_e}{l5_m} {l5_l} {l5_k}{l5_c}"

        # Line 6: Bottom horizontal (D1, D2)
        l6_d1 = self.chars["h_bar"] * 2 if d1 else "  "
        l6_d2 = self.chars["h_bar"] * 2 if d2 else "  "
        line6 = f" {l6_d1} {l6_d2} "

        return [line0, line1, line2, line3, line4, line5, line6]

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display the given data on the virtual 14-segment display.

        :param data: A list of 4 integers representing segment values.
        :param colon: Boolean flag whether to display the colon.
        """
        if not isinstance(data, list) or len(data) != 4:
            raise ValueError("Display data must be a list of 4 integers")

        self.current_display = data.copy()
        self._print_display(colon=colon)

    def clear(self) -> None:
        """Clear the display."""
        self.current_display = [0, 0, 0, 0]
        self._print_display()

    def _print_display(self, colon: bool = False) -> None:
        """
        Print the current 14-segment display to terminal.

        :param colon: Boolean flag for colon display.
        """
        # Render each digit
        digits = []
        for i, value in enumerate(self.current_display):
            digit = self._render_14seg_digit(value)

            # Add colon after second digit
            if i == 1:
                colon_str = self.chars["colon"] if colon else " "
                # Add colon spacing to middle lines
                digit[0] = digit[0] + "  "
                digit[1] = digit[1] + "  "
                digit[2] = digit[2] + "  "
                digit[3] = digit[3] + " " + colon_str
                digit[4] = digit[4] + "  "
                digit[5] = digit[5] + "  "
                digit[6] = digit[6] + "  "

            digits.append(digit)

        # Combine digits horizontally
        display_lines = []
        for row in range(self.display_height):
            line = ""
            for digit_idx in range(4):
                line += digits[digit_idx][row]
                if digit_idx < 3 and not (digit_idx == 1 and 0 <= row < 7):
                    line += " "
            display_lines.append(line)

        # Print with cursor management for in-place updates
        if self.is_first_display:
            print("\n" + "\n".join(display_lines) + "\n")
            self.is_first_display = False
        else:
            # Move cursor up and overwrite previous display
            sys.stdout.write(f"\033[{self.display_height + 2}A")
            print("\n" + "\n".join(display_lines) + "\n")
            sys.stdout.flush()
