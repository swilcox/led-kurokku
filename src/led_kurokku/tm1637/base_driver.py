class BaseDriver:
    """
    Base class for TM1637 driver.
    """

    def __init__(self, brightness=2) -> None:
        """
        Initialize the TM1637 driver.
        """
        self._brightness = brightness
        self._driver_name = "base"

    @property
    def name(self):
        return self._driver_name

    def display(self, data: list[int], colon: bool = False) -> None:
        """
        Display the given data on the TM1637 display.

        :param data: A list of integers to display.
        :param colon: boolean flag whether to display the colon.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def clear(self) -> None:
        """
        Clear the display.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def brightness(self) -> int:
        """
        Get the current brightness level of the display.

        :return: The brightness level (0-7).
        """
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        """
        Set the brightness level of the display.

        :param value: The brightness level (0-7).
        """
        if 0 <= value <= 7:
            self._brightness = value
        else:
            raise ValueError("Brightness must be between 0 and 7")
