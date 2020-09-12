"""Utilities and helpers for connecting and interacting with a SUMO instance over TCP."""
import ipaddress
import socket
from typing import Tuple


class SumoTcpConnection:
    """Manages a SUMO TCP connection and facilitates payload generation and response parsing."""

    class SumoSocketError(Exception):
        """Raised when something goes wrong with the SUMO socket."""

    _address: Tuple[ipaddress.IPv4Address, int]
    _socket: socket.socket

    def __init__(self, host: ipaddress.IPv4Address, port: int) -> None:
        """Initialize a connection over TCP to a SUMO process.

        Does not establish the connection (i.e. connect) until :meth:`~.connect` is called.

        :param host: IP address at which the connection should be established.
        :param port: Port number the SUMO process is listening to.
        """
        self._address = (host, port)
        self._socket = socket.socket()

    @property
    def address(self) -> Tuple[ipaddress.IPv4Address, int]:
        """Get the address this SUMO connection is with.

        :returns: SUMO executable host and port as a tuple in that order.
        """
        return (self._address[0], self._address[1])

    @property
    def socket(self) -> socket.socket:
        """Get the initialized socket that connects the SUMO process.

        The returned socket is not guaranteed to be open, only that it exists.

        :return: The initialized TCP socket with the SUMO process.
        """
        return self._socket

    def connect(self) -> None:
        """Establish a TCP connection to the SUMO process by connecting a socket.

        :raises SumoSocketError: Something went wrong when establishing the SUMO socket connection. The error is more
            specialized, check out the `socket.socket.connect documentation`_ for more details.

        .. _`socket.socket.connect documentation`: https://docs.python.org/3/library/socket.html#socket.socket.connect
        """
        try:
            self._socket.connect((str(self.address[0]), self.address[1]))
        except OSError as e:
            raise self.SumoSocketError(e)
