"""Generate the SVG plots used by raport.md using only the Python standard library."""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape


V0 = 53.0
ANGLE_DEG = 77.0
G = 9.81
MASS = 0.145
DIAMETER = 0.073
DRAG_COEFFICIENT = 0.47
AIR_DENSITY = 1.225
TIME_STEP = 0.002
OUTPUT_DIR = Path(__file__).parent / "files"


def derivative(state: tuple[float, ...], drag_factor: float) -> tuple[float, ...]:
    _, _, vx, vy = state
    speed = math.hypot(vx, vy)
    return (
        vx,
        vy,
        -drag_factor * speed * vx,
        -G - drag_factor * speed * vy,
    )


def add_scaled(
    state: tuple[float, ...], slope: tuple[float, ...], scale: float
) -> tuple[float, ...]:
    return tuple(value + scale * change for value, change in zip(state, slope))


def rk4_step(state: tuple[float, ...], step: float, drag_factor: float) -> tuple[float, ...]:
    first = derivative(state, drag_factor)
    second = derivative(add_scaled(state, first, step / 2), drag_factor)
    third = derivative(add_scaled(state, second, step / 2), drag_factor)
    fourth = derivative(add_scaled(state, third, step), drag_factor)
    return tuple(
        value
        + step
        * (k1 + 2 * k2 + 2 * k3 + k4)
        / 6
        for value, k1, k2, k3, k4 in zip(state, first, second, third, fourth)
    )


def simulate(drag_factor: float) -> list[tuple[float, ...]]:
    angle = math.radians(ANGLE_DEG)
    state = (0.0, 0.0, V0 * math.cos(angle), V0 * math.sin(angle))
    samples = [(0.0, *state)]
    time = 0.0
    while time < 30:
        next_state = rk4_step(state, TIME_STEP, drag_factor)
        next_time = time + TIME_STEP
        if next_state[1] <= 0 and next_state[3] < 0:
            fraction = state[1] / (state[1] - next_state[1])
            landing = tuple(
                start + fraction * (end - start)
                for start, end in zip(state, next_state)
            )
            samples.append((time + fraction * TIME_STEP, *landing))
            return samples
        state = next_state
        time = next_time
        samples.append((time, *state))
    raise RuntimeError("The simulation did not reach the ground within 30 seconds.")


def nice_number(value: float) -> str:
    if abs(value) < 1e-12:
        value = 0.0
    return f"{value:.3g}".replace("-", "−")


def chart(
    filename: str,
    title: str,
    x_label: str,
    y_label: str,
    series: list[tuple[str, list[tuple[float, float]], str]],
) -> None:
    width, height = 1000, 610
    left, top, plot_width, plot_height = 92, 75, 670, 440
    all_points = [point for _, points, _ in series for point in points]
    x_min = min(point[0] for point in all_points)
    x_max = max(point[0] for point in all_points)
    y_min = min(point[1] for point in all_points)
    y_max = max(point[1] for point in all_points)
    if y_min >= 0:
        y_min = 0.0
    if y_max == y_min:
        y_max = y_min + 1
    y_padding = (y_max - y_min) * 0.06
    y_min -= y_padding
    y_max += y_padding
    if y_min < 0 and min(point[1] for point in all_points) >= 0:
        y_min = 0.0

    def px(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * plot_width

    def py(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="DejaVu Sans, Arial, sans-serif" fill="#222">',
        f'<text x="{width / 2}" y="35" text-anchor="middle" font-size="21" font-weight="bold">{escape(title)}</text>',
    ]
    for index in range(6):
        x = x_min + (x_max - x_min) * index / 5
        y = y_min + (y_max - y_min) * index / 5
        x_pos, y_pos = px(x), py(y)
        parts.extend(
            [
                f'<line x1="{x_pos:.2f}" y1="{top}" x2="{x_pos:.2f}" y2="{top + plot_height}" stroke="#e5e7eb"/>',
                f'<line x1="{left}" y1="{y_pos:.2f}" x2="{left + plot_width}" y2="{y_pos:.2f}" stroke="#e5e7eb"/>',
                f'<text x="{x_pos:.2f}" y="{top + plot_height + 24}" text-anchor="middle" font-size="13">{nice_number(x)}</text>',
                f'<text x="{left - 12}" y="{y_pos + 4:.2f}" text-anchor="end" font-size="13">{nice_number(y)}</text>',
            ]
        )
    parts.extend(
        [
            f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#333"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 24}" text-anchor="middle" font-size="16">{escape(x_label)}</text>',
            f'<text x="23" y="{top + plot_height / 2}" text-anchor="middle" font-size="16" transform="rotate(-90 23 {top + plot_height / 2})">{escape(y_label)}</text>',
        ]
    )
    for index, (label, points, color) in enumerate(series):
        stride = max(1, len(points) // 1400)
        sampled = points[::stride]
        if sampled[-1] != points[-1]:
            sampled.append(points[-1])
        coordinates = " ".join(f"{px(x):.2f},{py(y):.2f}" for x, y in sampled)
        parts.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        legend_y = top + 28 + index * 29
        parts.extend(
            [
                f'<line x1="790" y1="{legend_y}" x2="826" y2="{legend_y}" stroke="{color}" stroke-width="3"/>',
                f'<text x="836" y="{legend_y + 5}" font-size="14">{escape(label)}</text>',
            ]
        )
    parts.extend(["</g>", "</svg>"])
    (OUTPUT_DIR / filename).write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    area = math.pi * DIAMETER**2 / 4
    drag_factor = AIR_DENSITY * DRAG_COEFFICIENT * area / (2 * MASS)
    no_drag = simulate(0.0)
    with_drag = simulate(drag_factor)

    def position_y(samples: list[tuple[float, ...]]) -> list[tuple[float, float]]:
        return [(sample[0], sample[2]) for sample in samples]

    def velocity_x(samples: list[tuple[float, ...]]) -> list[tuple[float, float]]:
        return [(sample[0], sample[3]) for sample in samples]

    def velocity_y(samples: list[tuple[float, ...]]) -> list[tuple[float, float]]:
        return [(sample[0], sample[4]) for sample in samples]

    def energy(samples: list[tuple[float, ...]]) -> list[tuple[float, float]]:
        return [
            (
                sample[0],
                MASS
                * (sample[3] ** 2 + sample[4] ** 2)
                / 2
                + MASS * G * sample[2],
            )
            for sample in samples
        ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chart(
        "tor_ruchu.svg",
        "Tor ruchu: próżnia i opór kwadratowy",
        "x [m]",
        "y [m]",
        [
        ("bez oporu", [(sample[1], sample[2]) for sample in no_drag], "#1769aa"),
        ("z oporem", [(sample[1], sample[2]) for sample in with_drag], "#d1495b"),
        ],
    )
    chart(
        "polozenie_czas.svg",
        "Położenie w funkcji czasu",
        "t [s]",
        "położenie [m]",
        [
            ("x, bez oporu", [(sample[0], sample[1]) for sample in no_drag], "#1769aa"),
            ("y, bez oporu", position_y(no_drag), "#56a3d9"),
            ("x, z oporem", [(sample[0], sample[1]) for sample in with_drag], "#d1495b"),
            ("y, z oporem", position_y(with_drag), "#f29e4c"),
        ],
    )
    chart(
        "predkosc_czas.svg",
        "Składowe prędkości w funkcji czasu",
        "t [s]",
        "prędkość [m/s]",
        [
            ("vx, bez oporu", velocity_x(no_drag), "#1769aa"),
            ("vy, bez oporu", velocity_y(no_drag), "#56a3d9"),
            ("vx, z oporem", velocity_x(with_drag), "#d1495b"),
            ("vy, z oporem", velocity_y(with_drag), "#f29e4c"),
        ],
    )
    chart(
        "energia_czas.svg",
        "Energia mechaniczna w funkcji czasu",
        "t [s]",
        "energia [J]",
        [
            ("bez oporu", energy(no_drag), "#1769aa"),
            ("z oporem", energy(with_drag), "#d1495b"),
        ],
    )

    vacuum_time = 2 * V0 * math.sin(math.radians(ANGLE_DEG)) / G
    vacuum_range = V0 * math.cos(math.radians(ANGLE_DEG)) * vacuum_time
    vacuum_height = (V0 * math.sin(math.radians(ANGLE_DEG))) ** 2 / (2 * G)
    print(f"Area: {area:.6f} m^2")
    print(f"Drag factor: {drag_factor:.8f} 1/m")
    print(f"No-drag flight time: {vacuum_time:.4f} s")
    print(f"No-drag range: {vacuum_range:.4f} m")
    print(f"No-drag maximum height: {vacuum_height:.4f} m")
    print(f"Drag flight time: {with_drag[-1][0]:.4f} s")
    print(f"Drag range: {with_drag[-1][1]:.4f} m")
    print(f"Drag maximum height: {max(sample[2] for sample in with_drag):.4f} m")
    print(f"Figures saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
