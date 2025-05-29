from copy import copy
from enum import IntEnum
import math
from typing import Final, Literal, NewType, Optional, TypedDict

from l2g.dol_system import DOLSystem, Symbol


FEED_RATE: Final[float] = 400
type Radian = float
type GCodeProgram = list[GCodeInstruction]


class Vector2D:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Position3D:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def add(self, v: Vector2D) -> "Position3D":
        return Position3D(self.x + v.x, self.y + v.y, self.z)

    def build(self) -> str:
        ndigits = 2
        return f"X{round(self.x, ndigits=ndigits)} Y{round(self.y, ndigits=ndigits)} Z{round(self.z, ndigits=ndigits)}"


class Command(IntEnum):
    RAPID_POSITIONING = 0
    LINEAR_INTERPOLATION = 1


class GCodeInstruction:
    def __init__(
        self, command: Command, dst_pos: Position3D, feed_rate: Optional[float] = None
    ):
        self.dst_pos = dst_pos
        self.command = command
        self.feed_rate = feed_rate

    def build(self):
        out = f"G{self.command:02} {self.dst_pos.build()}"
        if not self.feed_rate is None:
            out += f" F{self.feed_rate}"
        return out


class Orientation:
    def __init__(self, angle: Radian):
        self.angle = angle % math.tau

    def quarter_turn(self, direction: Literal[-1, 1] = 1) -> "Orientation":
        return Orientation(self.angle + direction * math.pi / 2)

    def angle_increment(self, angle_increment: Radian) -> "Orientation":
        return Orientation(self.angle + angle_increment)

    def to_vector(self, scale: float) -> Vector2D:
        return Vector2D(scale * math.cos(self.angle), scale * math.sin(self.angle))


class PositionRange:
    def __init__(self, min: float = math.inf, max: float = -math.inf):
        self.min = min
        self.max = max
    
    def update(self, curr_pos: float) -> "PositionRange":
        if curr_pos < self.min:
            return PositionRange(min=curr_pos, max=self.max)
        elif curr_pos > self.max:
            return PositionRange(min=self.min, max=curr_pos)
        else:
            return self
    
    def __str__(self):
        return f"(min={self.min:.2f}, max={self.max:.2f})"

type ProgramWithMeta = tuple[GCodeProgram, PositionRange, PositionRange]

def build_g_code(
    symbols: list[Symbol], angle_increment: Radian, step_size: float, init_angle: Radian = 0
) -> ProgramWithMeta:
    curr_orientation: Orientation = Orientation(init_angle)
    curr_pos: Position3D = Position3D(z=-1)
    x_range: PositionRange = PositionRange()
    y_range: PositionRange = PositionRange()
    program = []
    for s in symbols:
        if s == "+":
            curr_orientation = curr_orientation.angle_increment(angle_increment)
        elif s == "-":
            curr_orientation = curr_orientation.angle_increment(-angle_increment)
        elif s == "F" or s == "G":
            curr_pos = curr_pos.add(curr_orientation.to_vector(step_size))
        else:
            # A and B are ignored during drawing
            continue

        x_range = x_range.update(curr_pos.x)
        y_range = y_range.update(curr_pos.y)
        program.append(
            GCodeInstruction(
                command=Command.LINEAR_INTERPOLATION,
                dst_pos=curr_pos,
                feed_rate=FEED_RATE,
            )
        )
    return (program, x_range, y_range)


def compile_program(
    system: DOLSystem, nb_iterations: int, angle_increment: Radian, step_size: float, init_angle: Radian = 0
) -> ProgramWithMeta:
    symbols = system.nth_iteration(nb_iterations)
    return build_g_code(symbols, angle_increment, step_size, init_angle)


def write_nc(program: ProgramWithMeta, file_name: str) -> None:
    (code, x_range, y_range) = program
    lines: list[str] = [
        f"; x_range = {x_range}",
        f"; y_range = {y_range}",
        "M3 S10000",  # Start spinning at 10000 rpm
        "G90",  # Absolute mode
        "G21",  # Metric mode (locations in millimeters)
        GCodeInstruction(Command.RAPID_POSITIONING, dst_pos=Position3D(z=10)).build(),
        GCodeInstruction(Command.LINEAR_INTERPOLATION, dst_pos=Position3D(z=-1)).build(),
    ]
    lines += list(map(lambda i: i.build(), code))
    # Move the tool up out of the material
    last_pos = copy(code[-1].dst_pos)
    last_pos.z = 5
    lines.append(GCodeInstruction(Command.RAPID_POSITIONING, dst_pos=last_pos).build())
    # Stop the tool spinning
    lines.append("M5")
    file_path = f"./build/{file_name}.nc"
    with open(file_path, "w") as file:
        file.write("\n".join(lines))

    print(f"Wrote to '{file_path}'")
