import math
from typing import Final
from l2g.code_gen import (
    ProgramWithMeta,
    compile_program,
    deg_to_rad,
    write_nc,
)
from l2g.l_system import LSystem


# KOCH_CURVE: Final[ProgramWithMeta] = compile_program(
#     system=LSystem(
#         axiom=["F"],
#         production_rules={"F": ["F", "+", "F", "-", "F", "-", "F", "+", "F"]},
#     ),
#     nb_iterations=3,
#     angle_increment=math.pi / 2,
#     step_size=5,
# )

# HILBERT_CURVE: Final[ProgramWithMeta] = compile_program(
#     system=LSystem(
#         axiom=["A"],
#         production_rules={
#             "A": ["+", "B", "F", "-", "A", "F", "A", "-", "F", "B", "+"],
#             "B": ["-", "A", "F", "+", "B", "F", "B", "+", "F", "A", "-"],
#         },
#     ),
#     nb_iterations=5,
#     angle_increment=math.pi / 2,
#     step_size=5,
# )

# SIERPINSKY_TRIANGLE: Final[ProgramWithMeta] = compile_program(
#     system=LSystem(
#         axiom=["F", "-", "G", "-", "G"],
#         production_rules={
#             "F": ["F", "-", "G", "+", "F", "+", "G", "-", "F"],
#             "G": ["G", "G"],
#         },
#     ),
#     nb_iterations=5,
#     angle_increment=math.pi * 2 / 3,
#     step_size=4,
#     init_angle=math.pi/2
# )

BARNSLEY_FERN: Final[ProgramWithMeta] = compile_program(
    system=LSystem(
        axiom=["-", "X"],
        production_rules={
            "X": ["F", "+", "[", "[", "X", "]", "-", "X", "]", "-", "F", "[", "-", "F", "X", "]", "+", "X"],
            "F": ["F", "F"]
        }
    ),
    angle_increment=deg_to_rad(25),
    init_angle=math.pi/2-0.1,
    nb_iterations=5,
    step_size=2.2
)

if __name__ == "__main__":
    # write_nc(KOCH_CURVE, "koch")
    # write_nc(HILBERT_CURVE, "hilbert")
    # write_nc(SIERPINSKY_TRIANGLE, "sierpinsky")
    write_nc(BARNSLEY_FERN, "barnsley")
