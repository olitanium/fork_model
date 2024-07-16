from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Callable,
    TypeVar,
    Any,
    Generic,
    Self,
    Optional,
    Generator,
    final,
)
from abc import ABC, abstractmethod
import copy

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison

Hint_T = TypeVar("Hint_T")
Score_T = TypeVar("Score_T", bound="SupportsRichComparison")
Model_T = TypeVar("Model_T", bound="Model[Any, Any]")
Env_T = TypeVar("Env_T", bound="Environment")

CodeLine = Callable[[Model_T, Optional[Hint_T], Env_T], list[Hint_T]]


class Model(Generic[Score_T, Env_T], ABC): # Model trait
    """Model trait, inherit from this class and implement the `score` method.
    This will allow you to use this as a Model in the program, """
    __slots__ = ()

    @abstractmethod
    def score(self) -> Score_T:
        raise Exception("Dev must override Model.score")


class Environment(ABC): # Enviroment trait
    """This environment represents shared state between all models. It could store data
    about the structure of the model, or lookups. The state can be mutated after all
    models (and their descendents) have run one time-step.

    The only requirement for a type to inherit Environment is that it implements the
    `update` method, to update the internal state each round. The `Environment`
    implementor must include it's own synchronisation (such as a counter) to ensure
    that updates happen at the correct time  
    """
    __slots__ = ()

    @abstractmethod
    def update(self) -> None:
        raise Exception("Dev must override Environment.score")


@final
class Process(Generic[Model_T, Hint_T, Env_T]):
    __slots__ = ["__resume_ptr", "__hint", "__model"]

    def __init__(self, _model: Model_T, _hint: Optional[Hint_T] = None):
        self.__resume_ptr = 0
        self.__hint = _hint
        self.__model = _model

    def clone(self, resume_ptr: int, hint: Hint_T) -> Self:
        output = copy.deepcopy(self)
        output.__resume_ptr = resume_ptr
        output.__hint = hint
        return output

    def score(self):
        return self.__model.score()

    def execute(self, sys: Sys[Model_T, Hint_T, Env_T], env: Env_T):
        for line, instruction in sys.instructions_from(self.__resume_ptr):
            hint_list = instruction(self.__model, self.__hint, env)

            try:
                self.__hint = hint_list.pop()
            except IndexError:
                self.__hint = None

            for hint in hint_list:
                sys.add_model(self.clone(line + 1, hint))

        self.__resume_ptr = 0

@final
class Sys(Generic[Model_T, Hint_T, Env_T]):
    __slots__ = ["__process_list", "__code", "__capacity"]

    def __init__(
        self,
        initial: Model_T,
        code: list[CodeLine[Model_T, Hint_T, Env_T]],
    ):
        self.__process_list = [Process[Model_T, Hint_T, Env_T](initial)]
        self.__code = code

    def add_model(self, process: Process[Model_T, Hint_T, Env_T]):
        self.__process_list.append(process)

    def instructions_from(
        self, index: int
    ) -> Generator[tuple[int, Callable[[Model_T, Hint_T | None, Env_T], list[Hint_T]]]]:
        for line, code in enumerate(self.__code[index:], start=index):
            yield (line, code)

    def prune(self, stride: int, final_count: int):
        if len(self.__process_list) <= final_count:
            return

        self.__process_list.sort(key=lambda process: process.score(), reverse=True)
        x = self.__process_list
        if len(x) <= final_count * stride:
            n = final_count - (len(x) - final_count) // (stride - 1)
            y = x[:n] + x[n::stride]
        else:
            new_stride = len(x) // final_count + 1
            y = x[::new_stride]

        self.__process_list = y

    def execute(self, env: Env_T):
        for process in self.__process_list:  # parallelize?
            process.execute(self, env)

@final
class OperatingSystem(Generic[Model_T, Hint_T, Env_T]):
    __slots__ = ["__sys", "__env"]

    def __init__(
        self,
        initial: Model_T,
        code: list[CodeLine[Model_T, Hint_T, Env_T]],
        env: Env_T,
    ):
        self.__sys = Sys(initial, code)
        self.__env = env

    def execute(self):
        self.__sys.execute(self.__env)
        self.__env.update()

    def prune(self, stride: int, final_count: int):
        self.__sys.prune(stride, final_count)