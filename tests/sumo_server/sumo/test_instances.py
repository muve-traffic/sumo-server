"""Tests for :mod:`~muve.sumo_server.sumo.instances`."""
from __future__ import annotations

import pathlib
import subprocess  # noqa: S404, security
from typing import Final
from unittest import mock

import libsumo  # type: ignore
import pytest

from muve.sumo_server.sumo.instances import LocalLibSumoInstance, LocalTcpSumoInstance, SumoInstance


class TestSumoInstance:
    NONEXISTENT_PATH: Final[pathlib.Path] = pathlib.Path("/this/path/does/not/exist")
    FAKE_PATH: Final[pathlib.Path] = pathlib.Path(__file__).absolute()

    def test_nonexistent_path_is_nonexistent(self) -> None:
        assert not self.NONEXISTENT_PATH.exists()

    def test_fake_path_exists(self) -> None:
        assert self.FAKE_PATH.exists()

    def test_init_fails(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            SumoInstance(config=pathlib.Path(""))


class TestLocalTcpSumoInstance(TestSumoInstance):
    PORT_NUMBER: Final[int] = 8800

    def init_instance(self) -> LocalTcpSumoInstance:
        config = TestSumoInstance.FAKE_PATH
        executable = TestSumoInstance.FAKE_PATH
        port = self.PORT_NUMBER
        return LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_init_succeeds(self) -> None:
        self.init_instance()

    def test_init_fails_when_no_config(self) -> None:
        config = TestSumoInstance.NONEXISTENT_PATH
        executable = TestSumoInstance.FAKE_PATH
        port = self.PORT_NUMBER

        with pytest.raises(ValueError, match="config"):
            LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_init_fails_when_no_executable(self) -> None:
        config = TestSumoInstance.FAKE_PATH
        executable = TestSumoInstance.NONEXISTENT_PATH
        port = self.PORT_NUMBER

        with pytest.raises(ValueError, match="executable"):
            LocalTcpSumoInstance(config=config, executable=executable, port=port)

    def test_spawn_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("subprocess.Popen") as mock_popen:
            instance._spawn()
            args = [
                str(TestSumoInstance.FAKE_PATH),
                LocalTcpSumoInstance._CONFIGURATION_FLAG,
                str(TestSumoInstance.FAKE_PATH),
                LocalTcpSumoInstance._PORT_NUMBER_FLAG,
                str(self.PORT_NUMBER),
                LocalTcpSumoInstance._NUM_CLIENTS_FLAG,
                str(LocalTcpSumoInstance._NUM_CLIENTS),
            ]
            mock_popen.assert_called_once_with(args)

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


class TestLocalLibSumoInstance:
    def init_instance(self) -> LocalLibSumoInstance:
        LocalLibSumoInstance._exists_started = False
        config = TestSumoInstance.FAKE_PATH
        return LocalLibSumoInstance(config=config)

    def test_init_succeeds(self) -> None:
        self.init_instance()

    def test_init_fails_when_no_config(self) -> None:
        config = TestSumoInstance.NONEXISTENT_PATH

        with pytest.raises(ValueError, match="config"):
            LocalLibSumoInstance(config=config)

    def test_start_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start") as mock_libsumo_start:
            instance.start()
            args = [
                "",
                LocalTcpSumoInstance._CONFIGURATION_FLAG,
                str(TestSumoInstance.FAKE_PATH),
            ]
            mock_libsumo_start.assert_called_once_with(args)

    def test_start_fails_when_already_started(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start") as mock_libsumo_start:
            instance.start()

            with pytest.raises(LocalLibSumoInstance.SumoStatusError, match="already started"):
                instance.start()

            mock_libsumo_start.assert_called_once()

    def test_start_fails_when_other_started(self) -> None:
        instance1 = self.init_instance()
        instance2 = self.init_instance()

        with mock.patch("libsumo.start") as mock_libsumo_start:
            instance1.start()

            with pytest.raises(LocalLibSumoInstance.SumoLibError, match="one simulation"):
                instance2.start()

            mock_libsumo_start.assert_called_once()

    def test_start_fails_when_lib_errors(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start") as mock_libsumo_start:
            mock_libsumo_start.side_effect = libsumo.TraCIException("")

            with pytest.raises(LocalLibSumoInstance.SumoLibError):
                instance.start()

            mock_libsumo_start.assert_called_once()

    def test_step_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start"):
            instance.start()

        with mock.patch("libsumo.simulation.step") as mock_libsumo_step:
            instance.step()

            mock_libsumo_step.assert_called_once()

    def test_step_fails_when_not_started(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.simulation.step") as mock_libsumo_step:
            with pytest.raises(LocalLibSumoInstance.SumoStatusError, match="not started"):
                instance.step()

            mock_libsumo_step.assert_not_called()

    def test_step_fails_and_stops_when_lib_errors(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start"):
            instance.start()

        with mock.patch("libsumo.simulation.step") as mock_libsumo_step, mock.patch.object(
            instance,
            "stop",
        ) as stop_mock:
            mock_libsumo_step.side_effect = libsumo.TraCIException("")

            with pytest.raises(LocalLibSumoInstance.SumoLibError):
                instance.step()

            mock_libsumo_step.assert_called_once()
            stop_mock.assert_called_once()

    def test_stop_succeeds(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start"):
            instance.start()

        with mock.patch("libsumo.simulation.close") as mock_libsumo_close:
            instance.stop()

            mock_libsumo_close.assert_called_once()

    def test_stop_fails_when_not_started(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.simulation.close") as mock_libsumo_close:
            with pytest.raises(LocalLibSumoInstance.SumoStatusError, match="not started"):
                instance.stop()

            mock_libsumo_close.assert_not_called()

    def test_stop_fails_when_lib_errors(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start"):
            instance.start()

        with mock.patch("libsumo.simulation.close") as mock_libsumo_close:
            mock_libsumo_close.side_effect = libsumo.TraCIException("")

            with pytest.raises(LocalLibSumoInstance.SumoLibError):
                instance.stop()

            mock_libsumo_close.assert_called_once()

    def test_start_step_stop_repeated_succeeds(self) -> None:
        instance = self.init_instance()

        for _ in range(3):
            with mock.patch("libsumo.start"):
                instance.start()
            with mock.patch("libsumo.simulation.step"):
                instance.step()
            with mock.patch("libsumo.simulation.close"):
                instance.stop()

    def test_start_step_stop_step_fails(self) -> None:
        instance = self.init_instance()

        with mock.patch("libsumo.start"):
            instance.start()
        with mock.patch("libsumo.simulation.step"):
            instance.step()
        with mock.patch("libsumo.simulation.close"):
            instance.stop()

        with mock.patch("libsumo.simulation.step"):
            with pytest.raises(LocalLibSumoInstance.SumoStatusError, match="not started"):
                instance.step()
