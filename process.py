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
Model_T = TypeVar("Model_T", bound="Model[Any]")
Env_T = TypeVar("Env_T", bound="Environment")

CodeLine = Callable[[Model_T, Optional[Hint_T], Env_T], list[Hint_T]]


class Model(Generic[Score_T], ABC): # Model trait
    """Model trait, inherit from thsi class and implement the `score` method.
    This will allow you to use this as a Model in the program, """
    __slots__ = ()

    @abstractmethod
    def score(self) -> Score_T:
        raise Exception("Dev must override Model.score")


class Environment(ABC): # Enviroment trait
    """Environment trait, inherit from this class and implement the `update` method. This will allow you """
    __slots__ = ()

    @abstractmethod
    def update(self) -> None:
        raise Exception("Dev must override Environment.score")


@final
class Process(Generic[Model_T, Hint_T, Env_T]):
    __slots__ = "__resume_ptr", "__hint", "__model"

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
    __slots__ = "__process_list", "__code", "__capacity"

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
    __slots__ = "__sys", "__env"

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


# ========== BEGIN USER CODE =========== #

if __name__ == "__main__":

    import random

    class MainEnvironment(Environment):
        __slots__ = "__clock"

        def __init__(self):
            self.__clock = 0

        def get_clock(self) -> int:
            return self.__clock

        def update(self):
            self.__clock = self.__clock + 1

    ModelHint = int

    class UniqueName:
        def __init__(self):
            self.value = random.randint(1_000, 9_999)

        def __deepcopy__(self, _) -> UniqueName:
            return UniqueName()

        def __repr__(self) -> str:
            return f"{self.value}"

    class MainModel(Model[ModelHint]):
        __slots__ = "unique_name", "value"

        def __init__(self):
            self.unique_name = UniqueName()
            self.value = 0

        def step_one_incr(self, hint: Optional[ModelHint], env: MainEnvironment) -> list[ModelHint]:
            """This step increments the internal value using the given hint"""

            if hint != None:
                self.value += hint

            return []

        def step_two_test(self, hint: Optional[ModelHint], env: MainEnvironment) -> list[ModelHint]:
            """This step intentionally ignores (and replaces) the input hint"""

            if self.value % 2 == 0:
                return [1, 2]
            else:
                return [3]

        def step_thr_incr(
            self, value: Optional[ModelHint], env: MainEnvironment
        ) -> list[ModelHint]:
            """as step one this increments the value, but here returns a different output"""

            if value != None:
                self.value += value
            return [1, 2]

        def step_fou_prin(
            self, value: Optional[ModelHint], env: MainEnvironment
        ) -> list[ModelHint]:
            """this prints the model details to the terminal"""
            print(f"{env.get_clock()}, {self.unique_name}, {self.score()}")

            # pass the value through to the next stage
            if value != None:
                return []# value]
            else:
                return []

        def score(self):
            return self.value

    def main():
        os = OperatingSystem(
            MainModel(),
            [
                MainModel.step_one_incr,
                MainModel.step_two_test,
                MainModel.step_thr_incr,
                MainModel.step_fou_prin,
            ],
            MainEnvironment(),
        )

        while True:
            print("loop")
            os.execute()
            os.prune(stride=10, final_count=50)

    main()