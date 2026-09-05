from dataclasses import dataclass
import pytest
from typing import Protocol, Annotated


from raceway.extractor import Extractor, Cabled


class IFile(Protocol):
    pass


type CabledFileService = Annotated[IFile, Cabled]


@dataclass
class PatternService:

    file0_api: IFile
    """ No cabled example, passes can_* check. """

    file1_api: Annotated[IFile, Cabled]
    """ As class example. """

    file2_api: Annotated[IFile, Cabled()]
    """ As empty instance example. """

    file3_api: Annotated[str, Cabled(IFile)]
    """ As instance with proto example. """

    file4_api: CabledFileService
    """ As type alias example. """


@dataclass
class ParamsService:

    file_params_api: Annotated[
        IFile,
        Cabled(
            key="test_key",
            attr="test_attr",
            call_args=("test_call_arg",),
            call_kwargs=(("test_call_kwarg", 1),),
        ),
    ]
    """ Kitchen sink of various configuration params. """


class TestExtract:

    @pytest.fixture
    def default_ex(self):
        # Used to be a tractor but its not anymore.
        return Extractor()

    def test_cabled_patterns(self, default_ex):
        dep_specs = default_ex.extract(PatternService)
        lookup = dict(dep_specs)
        for i in range(5):
            k = f"file{i}_api"
            assert k in lookup
            assert lookup[k].proto is IFile

    def test_cabled_params(self, default_ex):
        dep_specs = default_ex.extract(ParamsService)
        lookup = dict(dep_specs)
        assert "file_params_api" in lookup
        assert lookup["file_params_api"].key == "test_key"
        assert lookup["file_params_api"].attr == "test_attr"
        assert lookup["file_params_api"].call_args[0] == "test_call_arg"
        assert (
            lookup["file_params_api"].call_kwargs[0][0] == "test_call_kwarg"
            and lookup["file_params_api"].call_kwargs[0][1] == 1
        )
