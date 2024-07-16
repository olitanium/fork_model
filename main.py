from __future__ import annotations
if __name__ == "__main__":

    import random
    import fork
    from typing import Optional
    

    class MainEnvironment(fork.Environment):
        __slots__ = ["__clock"]

        def __init__(self):
            self.__clock = 0

        def get_clock(self) -> int:
            return self.__clock

        def update(self):
            """This method increments the internal clock"""
            self.__clock = self.__clock + 1

    ModelHint = int

    class MainModel(fork.Model[ModelHint, MainEnvironment]):
        __slots__ = ["unique_name", "value"]

        def __init__(self):
            self.unique_name = random.random()
            self.value = 0
        
        def score(self):
            return self.value

        def step_one_incr(self, hint: Optional[ModelHint], env: MainEnvironment) -> list[ModelHint]:
            """This step increments the internal value using the given hint"""

            if hint != None:
                self.value += hint

            return []

        def step_two_test(self) -> list[ModelHint]:
            """This step intentionally ignores (and replaces) the input hint"""

            if self.value % 2 == 0:
                return [1, 2]
            else:
                return [3]

        def step_thr_incr(self, hint: Optional[ModelHint], env: MainEnvironment) -> list[ModelHint]:
            """as step one this increments the value, but here returns a different output"""

            if hint != None:
                self.value += hint
            return [1, 2]

        def step_fou_prin(self, hint: Optional[ModelHint], env: MainEnvironment) -> list[ModelHint]:
            """this prints the model details to the terminal"""
            print(f"{env.get_clock()}, {self.unique_name:.3f}, {self.score()}")

            # pass the hint through to the next stage
            if hint != None:
                return [hint]
            else:
                return []
            
        def __deepcopy__(self, _) -> MainModel:
            out = MainModel()
            out.value = self.value
            return out


    def main():
        os = fork.OperatingSystem(
            MainModel(),
            [
                MainModel.step_one_incr,
                # Functions which don't need all inputs can be added as a lambda
                lambda self, _1, _2: self.step_two_test(),
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