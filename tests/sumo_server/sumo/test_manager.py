"""Tests for :mod:`~muve.sumo_server.sumo.manager`."""
import inspect
import pathlib
from typing import Final
from unittest import mock

import pytest

from muve.sumo_server.sumo.manager import SumoInstanceManager


@mock.patch("muve.sumo_server.sumo.manager.LocalTcpSumoInstance")
class TestSumoInstanceManager:
    FAKE_PATH: Final[pathlib.Path] = pathlib.Path(__file__).absolute()
    PORT_NUMBER: Final[int] = 9800

    def test_create_instance_succeeds(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)

        mocked_instance.assert_called_once_with(
            config=self.FAKE_PATH,
            executable=mock.ANY,
            port=mock.ANY,
        )

    def test_create_instance_succeeds_and_correct_port(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)

        mocked_instance.assert_called_once_with(
            config=self.FAKE_PATH,
            executable=mock.ANY,
            port=SumoInstanceManager._current_port_number - 1,
        )

    def test_create_instance_succeeds_with_executable_path(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH, executable=self.FAKE_PATH)

        mocked_instance.assert_called_once_with(
            config=self.FAKE_PATH,
            executable=self.FAKE_PATH,
            port=mock.ANY,
        )

    def test_create_instance_succeeds_with_custom_port_number(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]
        port = self.PORT_NUMBER

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH, port=port)

        mocked_instance.assert_called_once_with(
            config=self.FAKE_PATH,
            executable=mock.ANY,
            port=port,
        )

    def test_create_instance_fails_when_nonexistent_executable(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]
        port = self.PORT_NUMBER
        default_sumo_command = SumoInstanceManager.DEFAULT_SUMO_COMMAND_NAME

        SumoInstanceManager.DEFAULT_SUMO_COMMAND_NAME = "command_does_not_exist"
        with pytest.raises(SumoInstanceManager.SumoExecutableNotFound, match="sumo"):
            SumoInstanceManager.create_instance(
                name,
                config=self.FAKE_PATH,
                port=port,
            )

        SumoInstanceManager.DEFAULT_SUMO_COMMAND_NAME = default_sumo_command
        mocked_instance.assert_not_called()

    def test_create_instance_fails_when_name_exists(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)
        with pytest.raises(ValueError, match="already exists"):
            SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)

        mocked_instance.assert_called_once()

    def test_get_instance_succeeds(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)
        SumoInstanceManager.get_instance(name)

        mocked_instance.assert_called_once()

    def test_get_instance_fails_when_no_instance(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        with pytest.raises(ValueError, match="has not been created"):
            SumoInstanceManager.get_instance(name)

    def test_destroy_instance_succeeds(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        SumoInstanceManager.create_instance(name, config=self.FAKE_PATH)
        SumoInstanceManager.destroy_instance(name)

        mocked_instance.assert_called_once()
        mocked_instance.return_value.stop.assert_called_once()

    def test_destroy_instance_fails_when_nonexistent(self, mocked_instance: mock.MagicMock) -> None:
        name = inspect.stack()[0][3]

        with pytest.raises(ValueError, match="does not exist"):
            SumoInstanceManager.destroy_instance(name)
