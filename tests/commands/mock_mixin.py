from abc import ABC

from unittest.mock import patch, MagicMock, seal


class MockMixin(ABC):
    def init_mock_manager(self, command_class: type) -> None:
        self.command_class = command_class
        self.mock_manager = MagicMock()

    def seal_mocks(self) -> None:
        seal(self.mock_manager)

    def monkey_patch(self, target: type, custom_name: str | None = None) -> MagicMock:
        name = custom_name or target.__name__
        target_str = f"{self.command_class.__module__}.{name}"
        patcher = patch(target_str, spec_set=target)
        self.addCleanup(patcher.stop)
        mock = patcher.start()
        self.mock_manager.attach_mock(mock, name)
        return mock

    def create_mock(self, spec_set: type, custom_name: str | None = None) -> MagicMock:
        mock = MagicMock(spec_set=spec_set)
        self.mock_manager.attach_mock(mock, custom_name or spec_set.__name__)
        return mock
