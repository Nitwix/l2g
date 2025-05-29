from typing import Literal


type Symbol = Literal["A", "B", "X", "F", "G", "+", "-", "[", "]"]

type ProductionRules = dict[Symbol, list[Symbol]]



class LSystem:
    """
    Deterministic, context-free, L-system
    """

    def __init__(self, axiom: list[Symbol], production_rules: ProductionRules):
        self.axiom = axiom
        self.production_rules = production_rules

    def _next_str(self, curr: list[Symbol]) -> list[Symbol]:
        out: list[Symbol] = []
        for s in curr:
            if s in self.production_rules:
                out += self.production_rules[s]
            else:
                out.append(s)
        return out


    def nth_iteration(self, n: int) -> list[Symbol]:
        curr: list[Symbol] = self.axiom
        for _ in range(n):
            curr = self._next_str(curr)
        return curr