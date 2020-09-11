"""Tests for :mod:`~muve.sumo_server.sumo.tcp`."""
import ipaddress
from typing import Final
from unittest import mock

import pytest

from muve.sumo_server.sumo.tcp import SumoTcpConnection


class TestSumoTcpConnection:
    LOCAL_HOST: Final[ipaddress.IPv6Address] = ipaddress.IPv6Address("::1")
    PORT_NUMBER: Final[int] = 8800

    def init_local_connection(self) -> SumoTcpConnection:
        host = self.LOCAL_HOST
        port = self.PORT_NUMBER
        return SumoTcpConnection(host, port)

    def test_init_local_succeeds(self) -> None:
        self.init_local_connection()

    def test_local_address_consistent(self) -> None:
        connection = self.init_local_connection()
        address = connection.address

        assert address[0] == self.LOCAL_HOST
        assert address[1] == self.PORT_NUMBER

    def test_connect_succeeds(self) -> None:
        connection = self.init_local_connection()

        with mock.patch("socket.socket.connect"):
            connection.connect()

    def test_connect_fails_when_socket_fails(self) -> None:
        connection = self.init_local_connection()

        with mock.patch("socket.socket.connect") as mock_socket:
            mock_socket.side_effect = OSError

            with pytest.raises(SumoTcpConnection.SumoSocketError):
                connection.connect()

    def test_get_socket_succeeds(self) -> None:
        connection = self.init_local_connection()
        assert connection.socket is not None

    def test_get_socket_succeeds_when_established(self) -> None:
        connection = self.init_local_connection()

        with mock.patch("socket.socket.connect"):
            connection.connect()
            connection.socket
