"""Tests for :mod:`~muve.sumo_server.sumo.instances`."""
from __future__ import annotations

import pathlib
import subprocess  # noqa: S404, security
from typing import Final
from unittest import mock

import pytest

from muve.sumo_server.sumo.instances import LocalTcpSumoInstance, SumoInstance


class TestSumoInstance:
    def test_init_fails(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            SumoInstance(config=pathlib.Path(""))


class TestLocalTcpSumoInstance:
    NONEXISTENT_PATH: Final[pathlib.Path] = pathlib.Path("/this/path/does/not/exist")
    FAKE_PATH: Final[pathlib.Path] = pathlib.Path(__file__).absolute()
    PORT_NUMBER: Final[int] = 8800

    def init_instance(self) -> LocalTcpSumoInstance:
        config = self.FAKE_PATH
        executable = self.FAKE_PATH
        port = self.PORT_NUMBER
        return LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_nonexistent_path_is_nonexistent(self) -> None:
        assert not self.NONEXISTENT_PATH.exists()

    def test_fake_path_exists(self) -> None:
        assert self.FAKE_PATH.exists()

    def test_init_succeeds(self) -> None:
        self.init_instance()

    def test_init_fails_when_no_config(self) -> None:
        config = self.NONEXISTENT_PATH
        executable = self.FAKE_PATH
        port = self.PORT_NUMBER

        with pytest.raises(ValueError, match="config"):
            LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_init_fails_when_no_executable(self) -> None:
        config = self.FAKE_PATH
        executable = self.NONEXISTENT_PATH
        port = self.PORT_NUMBER

        with pytest.raises(ValueError, match="executable"):
            LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_spawn_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("subprocess.Popen"):
            instance.spawn()

    def test_spawn_fails_when_subprocess_fails(self) -> None:
        instance = self.init_instance()

        with mock.patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = subprocess.SubprocessError

            with pytest.raises(LocalTcpSumoInstance.SumoProcessError):
                instance._spawn()

            mock_popen.assert_called_once()

    def test_get_process_succeeds_when_spawned(self) -> None:
        instance = self.init_instance()

        with mock.patch("subprocess.Popen"):
            instance._spawn()

        assert instance.process is not None

    def test_get_process_fails_when_inactive(self) -> None:
        instance = self.init_instance()

        with pytest.raises(LocalTcpSumoInstance.SumoProcessError):
            instance.process

    def test_connect_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("muve.sumo_server.sumo.instances.SumoTcpConnection") as mock_connection:
            instance._connect()

            mock_connection.assert_called_once_with(mock.ANY, self.PORT_NUMBER)
            mock_connection.return_value.connect.assert_called_once()

    def test_get_connection_succeeds_when_connected(self) -> None:
        instance = self.init_instance()

        with mock.patch("muve.sumo_server.sumo.instances.SumoTcpConnection"):
            instance._connect()

        assert instance.connection is not None

    def test_get_connection_fails_when_unconnected(self) -> None:
        instance = self.init_instance()

        with pytest.raises(LocalTcpSumoInstance.SumoConnectionError):
            instance.connection

    def test_start_unimplemented(self) -> None:
        instance = self.init_instance()

        with mock.patch.object(instance, "_spawn") as mock_spawn, mock.patch.object(
            instance,
            "_connect",
        ) as mock_connect:
            instance.start()

            mock_spawn.assert_called_once()
            mock_connect.assert_called_once()

    def test_start_fails_when_already_started(self) -> None:
        instance = self.init_instance()

        with mock.patch.object(instance, "_spawn") as mock_spawn, mock.patch.object(
            instance,
            "_connect",
        ) as mock_connect:
            instance.start()

            with pytest.raises(LocalTcpSumoInstance.SumoStatusError, match="already started"):
                instance.start()

            mock_spawn.assert_called_once()
            mock_connect.assert_called_once()

    def test_step_unimplemented(self) -> None:
        instance = self.init_instance()

        with pytest.raises(NotImplementedError):
            instance.step()

    def test_stop_unimplemented(self) -> None:
        instance = self.init_instance()

        with pytest.raises(NotImplementedError):
            instance.stop()
