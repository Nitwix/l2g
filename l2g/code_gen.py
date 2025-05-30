from copy import copy
from dataclasses import dataclass
from enum import IntEnum
import math
from typing import Final, Literal, NewType, Optional, TypedDict

from l2g.l_system import LSystem, Symbol


FEED_RATE: Final[float] = 100
LINE_DEPTH: Final[float] = -0.5
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

    def __eq__(self, other):
        if isinstance(other, Position3D):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return False

    def add(self, v: Vector2D) -> "Position3D":
        return Position3D(self.x + v.x, self.y + v.y, self.z)

    def above(self, z: float = 3) -> "Position3D":
        return Position3D(self.x, self.y, z)

    def build(self) -> str:
        ndigits = 2
        return f"X{round(self.x, ndigits=ndigits)} Y{round(self.y, ndigits=ndigits)} Z{round(self.z, ndigits=ndigits)}"


class Command(IntEnum):
    RAPID_POSITIONING = 0
    LINEAR_INTERPOLATION = 1


class GCodeInstruction:
    def __init__(
        self,
        command: Command,
        dst_pos: Position3D,
        feed_rate: Optional[float] = FEED_RATE,
    ):
        self.dst_pos = dst_pos
        self.command = command
        self.feed_rate = feed_rate

    def build(self):
        out = f"G{self.command:02} {self.dst_pos.build()}"
        if not self.feed_rate is None and self.command != Command.RAPID_POSITIONING:
            out += f" F{self.feed_rate}"
        return out


class Orientation:
    def __init__(self, angle: Radian):
        self.angle = angle % math.tau

    def __eq__(self, other):
        if isinstance(other, Orientation):
            return self.angle == other.angle
        return False

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


@dataclass
class ProgramWithMeta:
    code: GCodeProgram
    x_range: PositionRange
    y_range: PositionRange
    nb_iterations: int
    step_size: float
    angle_increment: Radian
    init_angle: Radian


@dataclass
class TurtleState:
    position: Position3D
    orientation: Orientation

    def __eq__(self, other) -> bool:
        if isinstance(other, TurtleState):
            return (
                self.position == other.position
                and self.orientation == other.orientation
            )
        return False


def deg_to_rad(angle: float) -> Radian:
    return angle / 180 * math.pi


def build_g_code(
    symbols: list[Symbol],
    angle_increment: Radian,
    step_size: float,
    init_angle: Radian = 0,
) -> tuple[GCodeProgram, PositionRange, PositionRange]:
    state: TurtleState = TurtleState(
        position=Position3D(z=LINE_DEPTH), orientation=Orientation(init_angle)
    )
    stack: list[TurtleState] = []
    x_range: PositionRange = PositionRange()
    y_range: PositionRange = PositionRange()
    program = []
    for s in symbols:
        if s == "+":
            state.orientation = state.orientation.angle_increment(angle_increment)
            continue
        elif s == "-":
            state.orientation = state.orientation.angle_increment(-angle_increment)
            continue
        elif s == "F" or s == "G":
            state.position = state.position.add(state.orientation.to_vector(step_size))
        elif s == "[":
            # stack push
            stack.append(copy(state))
            continue
        elif s == "]":
            prev_state = stack.pop()
            if prev_state == state:
                # optimization: don't move if popped state same as current state
                continue
            above_curr = state.position.above()
            above_prev = prev_state.position.above()
            program += [
                # First, we move back up
                GCodeInstruction(command=Command.RAPID_POSITIONING, dst_pos=above_curr),
                # Then, we move above the previous position
                GCodeInstruction(command=Command.RAPID_POSITIONING, dst_pos=above_prev),
                # Then, we move back down to the previous position
                GCodeInstruction(
                    command=Command.LINEAR_INTERPOLATION, dst_pos=prev_state.position
                ),
            ]
            # reset the state to the state popped from the stack
            state = prev_state
            continue
        else:
            # A and B are ignored during drawing
            continue

        x_range = x_range.update(state.position.x)
        y_range = y_range.update(state.position.y)
        program.append(
            GCodeInstruction(
                command=Command.LINEAR_INTERPOLATION,
                dst_pos=state.position,
            )
        )
    return (program, x_range, y_range)


def compile_program(
    system: LSystem,
    nb_iterations: int,
    angle_increment: Radian,
    step_size: float,
    init_angle: Radian = 0,
) -> ProgramWithMeta:
    symbols = system.nth_iteration(nb_iterations)
    (code, x_range, y_range) = build_g_code(
        symbols=symbols,
        angle_increment=angle_increment,
        step_size=step_size,
        init_angle=init_angle,
    )
    return ProgramWithMeta(
        code=code,
        x_range=x_range,
        y_range=y_range,
        nb_iterations=nb_iterations,
        step_size=step_size,
        angle_increment=angle_increment,
        init_angle=init_angle,
    )


def write_nc(program: ProgramWithMeta, file_name: str) -> None:
    lines: list[str] = [
        f"; x_range = {program.x_range}",
        f"; y_range = {program.y_range}",
        "M3 S10000",  # Start spinning at 10000 rpm
        "G90",  # Absolute mode
        "G21",  # Metric mode (locations in millimeters)
        GCodeInstruction(
            Command.RAPID_POSITIONING, dst_pos=Position3D(z=10), feed_rate=None
        ).build(),
        GCodeInstruction(
            Command.LINEAR_INTERPOLATION, dst_pos=Position3D(z=LINE_DEPTH)
        ).build(),
    ]
    lines += list(map(lambda i: i.build(), program.code))
    # Move the tool up out of the material
    last_pos = copy(program.code[-1].dst_pos)
    last_pos.z = 5
    lines.append(GCodeInstruction(Command.RAPID_POSITIONING, dst_pos=last_pos).build())
    # Stop the tool spinning
    lines.append("M5")
    file_path = f"./build/{file_name}_n{program.nb_iterations}_s{program.step_size:.2f}_ia{program.init_angle:.2f}_ai{program.angle_increment:.2f}.nc"
    with open(file_path, "w") as file:
        file.write("\n".join(lines))

    print(f"Wrote to '{file_path}'")
