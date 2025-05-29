from copy import copy
from enum import IntEnum
from typing import Final, Literal, Optional


type Symbol = Literal["A", "B", "F", "+", "-"]

FEED_RATE: Final[float] = 400


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
        return f"X{self.x} Y{self.y} Z{self.z}"


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
        out += "\n"
        return out


class Orientation(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def left(self) -> "Orientation":
        return Orientation((self.value - 1 + 4) % 4)

    def right(self) -> "Orientation":
        return Orientation((self.value + 1 + 4) % 4)

    def to_vector(self, scale: float = 1) -> Vector2D:
        if self == Orientation.NORTH:
            return Vector2D(0, 1 * scale)
        elif self == Orientation.EAST:
            return Vector2D(1 * scale, 0)
        elif self == Orientation.SOUTH:
            return Vector2D(0, -1 * scale)
        elif self == Orientation.WEST:
            return Vector2D(-1 * scale, 0)


def next_str(curr: list[Symbol]) -> list[Symbol]:
    out: list[Symbol] = []
    for s in curr:
        if s == "A":
            out += ["+", "B", "F", "-", "A", "F", "A", "-", "F", "B", "+"]
        elif s == "B":
            out += ["-", "A", "F", "+", "B", "F", "B", "+", "F", "A", "-"]
        else:
            out.append(s)
    return out


def nth_iteration(n: int) -> list[Symbol]:
    curr: list[Symbol] = ["A"]
    for _ in range(n):
        curr = next_str(curr)
    return curr


def build_g_code(symbols: list[Symbol]) -> list[GCodeInstruction]:
    curr_orientation: Orientation = Orientation.EAST
    curr_pos: Position3D = Position3D(z=-1)
    instructions = []
    for s in symbols:
        if s == "+":
            curr_orientation = curr_orientation.left()
        elif s == "-":
            curr_orientation = curr_orientation.right()
        elif s == "F":
            curr_pos = curr_pos.add(curr_orientation.to_vector(5))
        else:
            # A and B are ignored during drawing
            continue
        instructions.append(
            GCodeInstruction(
                command=Command.LINEAR_INTERPOLATION,
                dst_pos=curr_pos,
                feed_rate=FEED_RATE,
            )
        )
    return instructions


def write_nc(instructions: list[GCodeInstruction]) -> None:
    lines: list[str] = [
        "M3\n",
        "G21\n",
        GCodeInstruction(Command.RAPID_POSITIONING, dst_pos=Position3D(z=5)).build(),
    ]
    lines += list(map(lambda i: i.build(), instructions))
    last_pos = copy(instructions[-1].dst_pos)
    last_pos.z = 5
    lines.append(GCodeInstruction(Command.RAPID_POSITIONING, dst_pos=last_pos).build())
    filename = "./build/hilbert.nc"
    with open(filename, "w") as file:
        file.writelines(lines)

    print(f"Wrote to '{filename}'")


symbols = nth_iteration(5)
instr = build_g_code(symbols)
write_nc(instr)
