"""SUMO instance management utilities and providers."""
import pathlib
import shutil
from typing import Callable, ClassVar, Dict, Final, Optional, TypeVar

from muve.sumo_server.sumo.instances import LocalLibSumoInstance, LocalTcpSumoInstance, SumoInstance

SumoInstanceType = TypeVar("SumoInstanceType", bound=SumoInstance)


class SumoInstanceManager:
    """Manages a collection of (local) SUMO instances.

    SUMO instances should be created and accessed through this interface. It handles proper creation, distribution, and
    destruction of the instances.

    Typically, this class will only be used for a single SUMO instance: the default one. But each relevant method also
    provides the opportunity to refer to other SUMO instances by their unique name.
    """

    class SumoExecutableNotFound(Exception):
        """Raised when a SUMO executable is not found, whether through a command or supplied path."""

    _DEFAULT_SUMO_COMMAND_NAME: Final[str] = "sumo"
    _DEFAULT_INSTANCE_NAME: Final[str] = "default"
    _STARTING_PORT_NUMBER: Final[int] = 8800

    _instances: ClassVar[Dict[str, SumoInstance]] = {}
    _current_port_number: ClassVar[int] = _STARTING_PORT_NUMBER

    @classmethod
    def create_local_tcp_instance(
        cls,
        name: str = _DEFAULT_INSTANCE_NAME,
        *,
        config: pathlib.Path,
        executable: Optional[pathlib.Path] = None,
        port: Optional[int] = None,
    ) -> LocalTcpSumoInstance:
        """Create a local SUMO instance with the given name interfaced over TCP.

        The :class:`~muve.sumo_server.sumo.instances.LocalTcpSumoInstance` class is used for the instance.

        The created SUMO instance is returned, but can be acquired subsequently using :meth:`~.get_instance`.

        :param name: Unique name to give the SUMO instance.
        :param config: Path to the `sumocfg`_ configuration file.
        :param executable: Path to the base `sumo`_ executable,
            if not supplied then an attempt to find the default SUMO executable is made.
        :param port: Port number to start and connect to the SUMO instance on,
            if not supplied then we choose a port that has not been seen before by this manager.

        :raises ValueError: A SUMO instance with the supplied name already exists.

        :return: The generated (local) SUMO instance.

        .. _`sumocfg`: https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
        .. _`sumo`: https://sumo.dlr.de/docs/sumo.html
        """
        if not executable:
            executable = cls._find_default_executable()
        if not port:
            port = cls._choose_port()

        # Get around some funky mypy typing issues by aliasing the non-None variables and using them in the lambda.
        # mypy gets confused because it thinks that the variables can change to None, since they are optional, down
        # the line before the function is called, but we know that is not the case and we enforce it here.
        _executable = executable
        _port = port

        def instance_factory(executable: pathlib.Path = _executable, port: int = _port) -> LocalTcpSumoInstance:
            # mypy struggles with understanding that exe
            return LocalTcpSumoInstance(config=config, executable=executable, port=port)

        try:
            return cls._create_instance(name, instance_factory)
        except ValueError:
            raise

    @classmethod
    def create_local_lib_instance(
        cls,
        name: str = _DEFAULT_INSTANCE_NAME,
        *,
        config: pathlib.Path,
    ) -> LocalLibSumoInstance:
        """Create a local SUMO instance with the given name interfaced through `libsumo`_.

        The :class:`~muve.sumo_server.sumo.instances.LocalLibSumoInstance` class is used for the instance.

        The created SUMO instance is returned, but can be acquired subsequently using :meth:`~.get_instance`.

        :param name: Unique name to give the SUMO instance.
        :param config: Path to the `sumocfg`_ configuration file.

        :raises ValueError: A SUMO instance with the supplied name already exists.

        :return: The generated (local) SUMO instance.

        .. _`sumocfg`: https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
        .. _`sumo`: https://sumo.dlr.de/docs/sumo.html
        .. _`libsumo`: https://sumo.dlr.de/docs/Libsumo.html
        """

        def instance_factory() -> LocalLibSumoInstance:
            return LocalLibSumoInstance(config=config)

        try:
            return cls._create_instance(name, instance_factory)
        except ValueError:
            raise

    @classmethod
    def get_instance(cls, name: str = _DEFAULT_INSTANCE_NAME) -> SumoInstance:
        """Get the managed SUMO instance with the given unique name, or the default instance if no name is supplied.

        Instances created by :meth:`~.create_instance` can be acquired here.

        :param name: Unique name associated with the SUMO instance.

        :raises ValueError: No managed SUMO instance with the supplied name.

        :return: The SUMO instance associated with the supplied name exists.
        """
        try:
            return cls._instances[name]
        except KeyError:
            raise ValueError(f"SUMO instance '{name}' has not been created")

    @classmethod
    def destroy_instance(cls, name: str = _DEFAULT_INSTANCE_NAME) -> None:
        """Destroy a SUMO instance.

        The SUMO instance associated with the supplied name is accessed and stopped then removed from management. Other
        SUMO instances can be subsequently created using the same name with no issues.

        :param name: Unique name associated with the SUMO instance.

        :raises ValueError: No managed SUMO instance with the supplied name exists.
        """
        try:
            instance = cls._instances.pop(name)
        except KeyError:
            raise ValueError(f"SUMO instance '{name}' does not exist")

        instance.stop()

    @classmethod
    def _create_instance(cls, name: str, instance_factory: Callable[[], SumoInstanceType]) -> SumoInstanceType:
        if name in cls._instances:
            raise ValueError(f"SUMO instance '{name}' already exists")

        instance = instance_factory()
        cls._instances[name] = instance
        return instance

    @classmethod
    def _find_default_executable(cls) -> pathlib.Path:
        if command := shutil.which(cls._DEFAULT_SUMO_COMMAND_NAME):
            return pathlib.Path(command)

        raise cls.SumoExecutableNotFound(
            "could not find default SUMO executable path, ensure that the `sumo` command can be run from the shell",
        )

    @classmethod
    def _choose_port(cls) -> int:
        port = cls._current_port_number
        cls._current_port_number += 1
        return port
