import math
from typing import Final
from l2g.code_gen import (
    GCodeInstruction,
    GCodeProgram,
    ProgramWithMeta,
    build_g_code,
    compile_program,
    write_nc,
)
from l2g.dol_system import DOLSystem


KOCH_CURVE: Final[ProgramWithMeta] = compile_program(
    system=DOLSystem(
        axiom=["F"],
        production_rules={"F": ["F", "+", "F", "-", "F", "-", "F", "+", "F"]},
    ),
    nb_iterations=3,
    angle_increment=math.pi / 2,
    step_size=5,
)

HILBERT_CURVE: Final[ProgramWithMeta] = compile_program(
    system=DOLSystem(
        axiom=["A"],
        production_rules={
            "A": ["+", "B", "F", "-", "A", "F", "A", "-", "F", "B", "+"],
            "B": ["-", "A", "F", "+", "B", "F", "B", "+", "F", "A", "-"],
        },
    ),
    nb_iterations=5,
    angle_increment=math.pi / 2,
    step_size=5,
)

SIERPINSKY_TRIANGLE: Final[ProgramWithMeta] = compile_program(
    system=DOLSystem(
        axiom=["F", "-", "G", "-", "G"],
        production_rules={
            "F": ["F", "-", "G", "+", "F", "+", "G", "-", "F"],
            "G": ["G", "G"],
        },
    ),
    nb_iterations=6,
    angle_increment=math.pi * 2 / 3,
    step_size=2,
    init_angle=math.pi/2
)

if __name__ == "__main__":
    write_nc(KOCH_CURVE, "koch")
    write_nc(HILBERT_CURVE, "hilbert")
    write_nc(SIERPINSKY_TRIANGLE, "sierpinsky")
