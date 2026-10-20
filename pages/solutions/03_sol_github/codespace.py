import math
import random
from pathlib import Path

segments = []
x_position = 0.0
y_position = 0.0
heading = 0.0

for x in range(500):
	distance = x + 50
	next_x = x_position + distance * math.cos(math.radians(heading))
	next_y = y_position - distance * math.sin(math.radians(heading))
	color = "#{:02x}{:02x}{:02x}".format(
		random.randint(0, 255),
		random.randint(0, 255),
		random.randint(0, 255),
	)
	segments.append((x_position, y_position, next_x, next_y, color))
	x_position = next_x
	y_position = next_y
	heading -= 91

min_x = min(min(segment[0], segment[2]) for segment in segments)
max_x = max(max(segment[0], segment[2]) for segment in segments)
min_y = min(min(segment[1], segment[3]) for segment in segments)
max_y = max(max(segment[1], segment[3]) for segment in segments)
padding = 20
view_x = min_x - padding
view_y = min_y - padding
view_width = max_x - min_x + 2 * padding
view_height = max_y - min_y + 2 * padding

svg_lines = [
	'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" '
	f'viewBox="{view_x} {view_y} {view_width} {view_height}">',
	'<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="black"/>'.format(
		view_x, view_y, view_width, view_height
	),
]
svg_lines.extend(
	'<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" '
	'stroke="{}" stroke-width="2" stroke-linecap="round"/>'.format(*segment)
	for segment in segments
)
svg_lines.append("</svg>")

output_path = Path(__file__).with_name("spirala.svg")
output_path.write_text("\n".join(svg_lines), encoding="utf-8")
print(f"Rysunek zapisano w pliku: {output_path}")
