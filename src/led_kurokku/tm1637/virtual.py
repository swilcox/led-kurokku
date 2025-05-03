import time
import os
import sys
from .base_driver import BaseDriver

class VirtualDriver(BaseDriver):
    """
    A terminal-based seven-segment display library.
    Supports displaying 4 digits with a colon after the second digit.
    Features in-place updating with ANSI escape codes.
    """
    
    def __init__(self):
        """Initialize the seven-segment display."""
        super().__init__()
        # Unicode characters for the segments
        self.segments = {
            "top_h": "━━",
            "middle_h": "━━",
            "bottom_h": "━━",
            "top_left_v": "┃",
            "top_right_v": "┃",
            "bottom_left_v": "┃",
            "bottom_right_v": "┃",
            "colon": "∶"
        }
        self._driver_name = "virtual"
        # Initialize with all segments off
        self.current_display = [0, 0, 0, 0]
        
        # Height of the display (number of lines)
        self.display_height = 5
        
        # Track if this is the first display
        self.is_first_display = True

    def _render_digit(self, segment_bits):
        """
        Render a single digit based on segment bits.
        
        Args:
            segment_bits: Integer representing which segments to light up.
                Bit 0 (LSB): Top horizontal
                Bit 1: Top right vertical
                Bit 2: Bottom right vertical
                Bit 3: Bottom horizontal
                Bit 4: Bottom left vertical
                Bit 5: Top left vertical
                Bit 6: Middle horizontal
        
        Returns:
            List of strings representing the lines of the digit.
        """
        # Helper function to check if a segment should be on
        def has_segment(position):
            return (segment_bits & (1 << position)) != 0
        
        # Build the digit character by character
        top = f" {self.segments['top_h']} " if has_segment(0) else "    "
        top_row = self.segments['top_left_v'] if has_segment(5) else " "
        top_row_end = self.segments['top_right_v'] if has_segment(1) else " "
        middle = f" {self.segments['middle_h']} " if has_segment(6) else "    "
        bottom_row = self.segments['bottom_left_v'] if has_segment(4) else " "
        bottom_row_end = self.segments['bottom_right_v'] if has_segment(2) else " "
        bottom = f" {self.segments['bottom_h']} " if has_segment(3) else "    "
        
        # Assemble the digit as an array of lines
        return [
            top,
            f"{top_row}  {top_row_end}",
            middle,
            f"{bottom_row}  {bottom_row_end}",
            bottom
        ]
    
    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display the values on the seven-segment display.
        Updates the display in-place using ANSI escape codes.
        
        Args:
            data: List of 4 integers, each representing the segments to light up
                for a digit in the display (bit-wise).
            colon: Boolean indicating whether or not to display a colon.
        
        Returns:
            The instance (self) for method chaining.
        """
        if not isinstance(data, list) or len(data) != 4:
            raise ValueError("Display method requires a list of 4 integers")
        
        self.current_display = data.copy()
        self._print_display(colon = colon)

    def clear(self):
        """
        Clear the display (turn off all segments).
        
        Returns:
            The instance (self) for method chaining.
        """
        self.current_display = [0, 0, 0, 0]
        self._print_display()
        
        return self  # Enable method chaining
    
    def _print_display(self, colon: bool = False) -> None:
        """Print the current display to the terminal, updating in-place."""
        # Render each digit
        digits = []
        for i, value in enumerate(self.current_display):
            # Get the rendered digit
            digit = self._render_digit(value)
            
            # Add colon after the second digit (index 1)
            colon_str = self.segments["colon"] if colon else " "
            if i == 1:
                digit[1] = digit[1] + " "
                digit[2] = digit[2] + colon_str
                digit[3] = digit[3] + " "
            
            digits.append(digit)
        
        # Combine digits horizontally, row by row
        display_lines = []
        for row in range(5):
            line = ""
            for digit_idx in range(4):
                line += digits[digit_idx][row]
                # Add space between digits, except after colon
                if digit_idx < 3 and not (digit_idx == 1 and 1 <= row <= 3):
                    line += " "
            
            display_lines.append(line)
        
        # For the first display, just print normally
        if self.is_first_display:
            print("\n" + "\n".join(display_lines) + "\n")
            self.is_first_display = False
        else:
            # For subsequent displays, move cursor up and overwrite
            # Move cursor up to the first line of the previous display
            # +2 for the blank lines before and after the display
            sys.stdout.write(f"\033[{self.display_height + 2}A")
            
            # Print the new display
            print("\n" + "\n".join(display_lines) + "\n")
            
            # Flush to ensure immediate display
            sys.stdout.flush()
