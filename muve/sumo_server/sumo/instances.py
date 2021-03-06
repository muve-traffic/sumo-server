"""Collection of SUMO instance management classes.

The classes in this module probably should not be instantiated directly, instead they should be created and managed by
objects from :mod:`~muve.sumo_server.sumo.manager`.
"""
from __future__ import annotations

import abc
import ipaddress
import os
import pathlib
import subprocess  # noqa: S404, security
from types import ModuleType
from typing import ClassVar, Final, List, Optional, TypeVar, Union
from unittest import mock

# libsumo refuses to install quickly for CI/CD unittests, if this environment variable is False just don't use it.
# The mocks in tests should take care of actually letting libsumo be called (mocked).
if not int(os.getenv("NO_LIBSUMO", False)):  # pragma: nocover
    import libsumo  # type: ignore
else:
    libsumo = mock.MagicMock()

from muve.sumo_server.sumo.tcp import SumoTcpConnection

StatusGuardedFuncType = TypeVar("StatusGuardedFuncType")


class SumoInstance(abc.ABC):
    """Abstract SUMO instance interface.

    This class cannot be instantiated, but should be extended to actually implement this interface.
    """

    class SumoStatusError(Exception):
        """Raised when a the status of the SUMO instance is incompatible with the operation called."""

    _CONFIGURATION_FLAG: Final[str] = "-c"

    _config: pathlib.Path
    _is_started: bool

    def __init__(self, *, config: pathlib.Path) -> None:
        """Initialize the abstract SUMO instance with a SUMO configuration.

        :param config: Path to the `sumocfg`_ configuration file.

        :raises ValueError: The provided configuration path does not exist.

        .. _`sumocfg`: https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
        """
        if not config.exists():
            raise ValueError(f"provided configuration file {config} does not exist")

        self._config = config
        self._is_started = False

    @property
    def config(self) -> pathlib.Path:
        """Get the path to the SUMO configuration file used by this instance.

        :returns: Path to the SUMO configuration.
        """
        return self._config

    @abc.abstractmethod
    def start(self) -> None:
        """Start the interaction with SUMO."""

    @abc.abstractmethod
    def step(self) -> None:
        """Step the SUMO simulation."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop the interaction with SUMO and clean up."""


class LocalTcpSumoInstance(SumoInstance):
    """Manages a single local SUMO process and the related TCP socket connection for communication.

    Do not manually instantiate this class, use
    :meth:`~muve.sumo_server.sumo.manager.SumoInstanceManager.create_instance` instead.
    """

    class SumoProcessError(Exception):
        """Raised when something goes wrong with the SUMO subprocess."""

    class SumoConnectionError(Exception):
        """Raised when something goes wrong with the SUMO connection."""

    LOCAL_HOST: Final[ipaddress.IPv4Address] = ipaddress.IPv4Address("127.0.0.1")
    _PORT_NUMBER_FLAG: Final[str] = "--remote-port"
    _NUM_CLIENTS_FLAG: Final[str] = "--num-clients"
    _NUM_CLIENTS: Final[int] = 1

    _executable: pathlib.Path
    _port: int
    _process: Optional[subprocess.Popen[bytes]]
    _connection: Optional[SumoTcpConnection]

    def __init__(self, *, config: pathlib.Path, executable: pathlib.Path, port: int) -> None:
        """Initialize a SUMO instance manager.

        :param config: Path to the `sumocfg`_ configuration file.
        :param executable: Path to the base SUMO executable.
        :param port: Port number to spawn and connect to the SUMO instance on.

        :raises ValueError: One or more of the provided paths does not exist.

        .. _`sumocfg`: https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
        """
        try:
            super().__init__(config=config)
        except ValueError:
            raise

        if not executable.exists():
            raise ValueError(f"provided executable file {executable} does not exist")

        self._config = config
        self._executable = executable
        self._port = port
        self._process = None
        self._connection = None

    @property
    def executable(self) -> pathlib.Path:
        """Get the path to the SUMO executable file used by this instance.

        :returns: Path to the SUMO executable.
        """
        return self._executable

    @property
    def port(self) -> int:
        """Get the port used by this instance to connect to the SUMO executable over TCP.

        :returns: SUMO executable TCP port.
        """
        return self._port

    @property
    def process(self) -> subprocess.Popen[bytes]:
        """Try to get the spawned SUMO process. Errors if the SUMO process does not exist.

        :raises SumoProcessError: Associated SUMO process does not exist.

        :return: The spawned SUMO subprocess.
        """
        if not self._process:
            raise self.SumoProcessError("SUMO process is not spawned")
        return self._process

    @property
    def connection(self) -> SumoTcpConnection:
        """Try to get the established SUMO process. Errors if the SUMO connection does not exist.

        :raises SumoConnectionError: Associated SUMO process is not connected.

        :return: The established SUMO TCP connection.
        """
        if not self._connection:
            raise self.SumoConnectionError("SUMO connection is not established")
        return self._connection

    def start(self) -> None:
        """Start the interaction with SUMO by spawning a SUMO subprocess and connecting to it.

        This effectively starts the simulation; however, it will not run. See :meth:`~.step` to run the simulation.

        :raises SumoStatusError: This instance is already running.
        """
        if self._is_started:
            raise self.SumoStatusError("this SUMO instance is already started")

        self._spawn()
        self._connect()

        self._is_started = True

    def step(self) -> None:
        """Step the SUMO simulation.

        :raises NotImplementedError: Not implemented.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the interaction with SUMO, stop the simulation, and close the connection.

        :raises NotImplementedError: Not implemented.
        """
        raise NotImplementedError

    def _spawn(self) -> None:
        """Spawn the SUMO process.

        :raises SumoProcessError: Something went wrong with creating the SUMO subprocess. The error is more
            specialized, check out the `subprocess exceptions documentation`_ for more details.

        .. _`subprocess exceptions documentation`: https://docs.python.org/3/library/subprocess.html#exceptions
        """
        args: List[Union[str, pathlib.Path]] = [
            str(self.executable),
            self._CONFIGURATION_FLAG,
            str(self.config),
            self._PORT_NUMBER_FLAG,
            str(self.port),
            self._NUM_CLIENTS_FLAG,
            str(self._NUM_CLIENTS),
        ]

        try:
            self._process = subprocess.Popen(args)  # noqa: S603, security
        except subprocess.SubprocessError as e:
            raise self.SumoProcessError(e)

    def _connect(self) -> None:
        """Connect to the SUMO instance over a TCP socket."""
        self._connection = SumoTcpConnection(self.LOCAL_HOST, self.port)
        self._connection.connect()


class LocalLibSumoInstance(SumoInstance):
    """Manages interactions with `libsumo`_ to provide an interface to SUMO.

    Do not manually instantiate this class, use
    :meth:`~muve.sumo_server.sumo.manager.SumoInstanceManager.create_instance` instead.

    .. _`libsumo`: https://sumo.dlr.de/docs/Libsumo.html
    """

    class SumoLibError(Exception):
        """Raised when something goes wrong with our interface to SUMO, `libsumo`."""

    _libsumo: Final[ModuleType] = libsumo

    _exists_started: ClassVar[bool] = False

    def __init__(self, *, config: pathlib.Path) -> None:
        """Initialize the `libsumo` SUMO instance with a SUMO configuration.

        :param config: Path to the `sumocfg`_ configuration file.

        :raises ValueError: The provided configuration path does not exist.

        .. _`sumocfg`: https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
        """
        try:
            super().__init__(config=config)
        except ValueError:
            raise

    def start(self) -> None:
        """Start the interaction with SUMO.

        :raises SumoStatusError: This instance is already running.
        :raises SumoLibError: Cannot start the interaction with the SUMO simulation.
        """
        if self._is_started:
            raise self.SumoStatusError("this SUMO instance is already started")
        if LocalLibSumoInstance._exists_started:
            raise self.SumoLibError("`libsumo` only supports one simulation running at a time")

        try:
            # The first argument (in the list) is typically the SUMO executable
            # but using libsumo do not need to provide it.
            # NOTE: consider using the `traceFile` argument here.
            self._libsumo.start(["", self._CONFIGURATION_FLAG, str(self.config)])  # type: ignore
        except self._libsumo.TraCIException as e:  # type: ignore
            self._is_started = False
            raise self.SumoLibError(e)  # type: ignore

        self._is_started = True
        LocalLibSumoInstance._exists_started = True

    def step(self) -> None:
        """Step the SUMO simulation.

        :raises SumoStatusError: This instance is not running.
        :raises SumoLibError: Stepping caused an exception with the SUMO library.
        """
        if not self._is_started:
            raise self.SumoStatusError("this SUMO instance is not started")

        try:
            # NOTE: this returns subscription values, consider parsing them.
            self._libsumo.simulation.step()  # type: ignore
        except self._libsumo.TraCIException as e:  # type: ignore
            self.stop()
            raise self.SumoLibError(e)  # type: ignore

    def stop(self) -> None:
        """Stop the interaction with SUMO which stops the simulation.

        :raises SumoStatusError: This instance is not running.
        :raises SumoLibError: Stopping caused an exception with the SUMO library.
        """
        if not self._is_started:
            raise self.SumoStatusError("this SUMO instance is not started")

        try:
            self._libsumo.close()  # type: ignore
        except self._libsumo.TraCIException as e:  # type: ignore
            raise self.SumoLibError(e)  # type: ignore
        finally:
            self._is_started = False
            LocalLibSumoInstance._exists_started = False
