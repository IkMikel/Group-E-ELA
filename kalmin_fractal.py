import turtle
import math
import random

# --- CONFIGURATION & CONSTANTS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = -0.5      # Pulls the string straight down
DAMPING = 0.95
NUM_ITERATIONS = 5
SWITCH_THRESHOLD = -240  # Trigger depth: pull lower than this to change tree color

# --- CUSTOM TREE COLORS SYSTEM ---
TREE_PALETTES = [
    ("#8B5A2B", "#2E8B57"),  # 0: Classic Brown & Green
    ("#4A2E80", "#FF007F"),  # 1: Cyberpunk Purple & Hot Pink
    ("#004411", "#00FFCC"),  # 2: Deep Emerald & Matrix Neon Mint
    ("#3A3A3A", "#FF4500"),  # 3: Industrial Charcoal & Volcano Orange
    ("#1A365D", "#FFD700")   # 4: Midnight Blue & Gold Leaves
]
current_palette_idx = 0
switch_primed = True  # Prevents multiple triggers during a single pull

# --- PURE PYTHON PERLIN NOISE IMPLEMENTATION ---


class PerlinNoise1D:
    def __init__(self):
        self.gradients = [random.uniform(-1, 1) for _ in range(256)]

    def noise(self, x):
        xf = x - math.floor(x)
        xi = int(math.floor(x)) & 255
        xi1 = (xi + 1) & 255
        u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
        n0 = self.gradients[xi] * xf
        n1 = self.gradients[xi1] * (xf - 1)
        return n0 + u * (n1 - n0)


wind_generator_x = PerlinNoise1D()
wind_generator_y = PerlinNoise1D()
noise_time = 0.0

# --- SCREEN SETUP ---
screen = turtle.Screen()
screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
screen.title("Gosper String Pull-Switch (Changes Fractal Tree Color!)")
screen.bgcolor("black")
screen.tracer(0)

# --- TURTLE SETUP ---
pen = turtle.Turtle()
pen.hideturtle()
pen.speed(0)

# --- GLOBAL STORAGE FOR HOOK POINT ---
string_hook_x = 0.0
string_hook_y = 0.0

# --- VERLET PHYSICS SETUP ---
num_points = 5
link_length = 30.0
points = []
dragged_point_idx = None


def init_physics_string(hx, hy):
    """Initializes the rope points directly beneath the tree branch tip."""
    global points
    points = []
    for i in range(num_points):
        px = hx
        py = hy - (i * link_length)
        is_pinned = (i == 0)
        points.append([px, py, px, py, is_pinned])


def update_physics():
    """Applies physics and checks if the string has been dragged down like a switch."""
    global points, dragged_point_idx, string_hook_x, string_hook_y, current_palette_idx, switch_primed
    if not points:
        return

    # Lock pinned node onto the dynamic windy branch tip
    points[0][0] = string_hook_x
    points[0][1] = string_hook_y
    points[0][2] = string_hook_x
    points[0][3] = string_hook_y

    # 1. Verlet Integration
    for idx, p in enumerate(points):
        if p[4]:
            continue  # Skip pinned node
        if idx == dragged_point_idx:
            continue  # Skip node held by mouse

        vx = (p[0] - p[2]) * DAMPING
        vy = (p[1] - p[3]) * DAMPING

        p[2], p[3] = p[0], p[1]
        p[0] += vx
        p[1] += vy + GRAVITY

    # 2. Length Constraints
    for _ in range(NUM_ITERATIONS):
        for i in range(num_points - 1):
            p1 = points[i]
            p2 = points[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            distance = math.hypot(dx, dy)
            if distance == 0:
                continue

            difference = link_length - distance
            percent = difference / distance / 2.0
            offset_x = dx * percent
            offset_y = dy * percent

            if not p1[4] and i != dragged_point_idx:
                p1[0] -= offset_x
                p1[1] -= offset_y
            if not p2[4] and (i+1) != dragged_point_idx:
                p2[0] += offset_x
                p2[1] += offset_y

    # 3. SWITCH LOGIC: Check the position of the handle (the end of the string)
    lowest_y = points[-1][1]
    if lowest_y < SWITCH_THRESHOLD:
        if switch_primed:
            # Cycle to the next color palette
            current_palette_idx = (
                current_palette_idx + 1) % len(TREE_PALETTES)
            switch_primed = False  # Deactivate until the user lets go or raises it
    elif lowest_y > SWITCH_THRESHOLD + 20:
        # Reset the switch spring once the string goes back up
        switch_primed = True


def draw_tree(x, y, angle, length, depth, time_offset):
    """Draws an 8-level tree that changes color based on the switch state."""
    if depth == 0 or length < 2:
        return

    # Perlin Noise wind adjustments
    wind_x = wind_generator_x.noise(time_offset + depth * 0.2) * 4.0
    wind_y = wind_generator_y.noise(time_offset + depth * 0.15) * 1.5

    rad = math.radians(angle)
    end_x = x + length * math.cos(rad) + wind_x
    end_y = y + length * math.sin(rad) + wind_y

    # Get colors from our currently switched palette
    trunk_color, leaf_color = TREE_PALETTES[current_palette_idx]
    pen.color(trunk_color if depth > 4 else leaf_color)
    pen.pensize(max(1, depth))

    pen.penup()
    pen.goto(x, y)
    pen.pendown()
    pen.goto(end_x, end_y)

    # Capture the location of a stable leaf node branch to attach the switch string
    global string_hook_x, string_hook_y
    if depth == 1:
        string_hook_x = end_x
        string_hook_y = end_y

    new_length = length * 0.76
    draw_tree(end_x, end_y, angle - 22 + (wind_x * 0.4),
              new_length, depth - 1, time_offset)
    draw_tree(end_x, end_y, angle + 22 + (wind_x * 0.4),
              new_length, depth - 1, time_offset)


def draw_gosper_segment(x1, y1, x2, y2, depth, turn_left=True):
    """Recursively parses a single continuous string path following Gosper geometry."""
    if depth == 0:
        pen.goto(x2, y2)
        return

    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    base_angle = math.atan2(dy, dx)

    gosper_scale = dist / math.sqrt(7)
    angle_offset = math.radians(19.106)

    if turn_left:
        current_angle = base_angle + angle_offset
    else:
        current_angle = base_angle - angle_offset

    steps = [0, 60, -60, -120, 0, 60,
             0] if turn_left else [0, -60, 0, 120, 60, -60, 0]
    states = [True, False, True, True, False, True, True] if turn_left else [
        False, False, True, False, True, True, False]

    curr_x, curr_y = x1, y1
    for step, state in zip(steps, states):
        if turn_left:
            current_angle += math.radians(step)
        else:
            current_angle -= math.radians(step)

        next_x = curr_x + gosper_scale * math.cos(current_angle)
        next_y = curr_y + gosper_scale * math.sin(current_angle)

        draw_gosper_segment(curr_x, curr_y, next_x, next_y, depth - 1, state)
        curr_x, curr_y = next_x, next_y


def render_scene():
    """Renders the screen frame by frame."""
    global string_hook_x, string_hook_y, noise_time
    pen.clear()

    noise_time += 0.02

    # 1. Render the 8-Level Tree
    draw_tree(x=0, y=-150, angle=90, length=65,
              depth=8, time_offset=noise_time)

    if not points and string_hook_x != 0.0:
        init_physics_string(string_hook_x, string_hook_y)

    # 2. Render the Single Continuous Gosper String
    if points:
        # String changes color when pulled low to signal the switch triggering
        if not switch_primed:
            pen.color("#FF0033")  # Red indicator if clicked / fully pulled
            pen.pensize(2)
        else:
            pen.color("#00FFFF")  # Default electric cyan string
            pen.pensize(1)

        pen.penup()
        pen.goto(points[0][0], points[0][1])
        pen.pendown()

        # Render the entire length of the physics nodes as one single continuous Gosper Curve
        # Set depth=1 or depth=2 for smooth dragging. Set depth=4 to view massive complexity.
        draw_gosper_segment(
            points[0][0], points[0][1], points[-1][0], points[-1][1], depth=2, turn_left=True)

        # Draw a little physical handle "pull knob" at the bottom node to show where to grab
        pen.penup()
        pen.goto(points[-1][0], points[-1][1])
        pen.pendown()
        pen.dot(8, "white")

    screen.update()

# --- MOUSE INTERACTION HANDLERS ---


def on_click(x, y):
    global dragged_point_idx
    if not points:
        return
    min_dist = 40.0

    for idx, p in enumerate(points):
        if p[4]:
            continue  # Ignore the top fixed point
        dist = math.hypot(p[0] - x, p[1] - y)
        if dist < min_dist:
            min_dist = dist
            dragged_point_idx = idx


def on_drag_canvas(event):
    global dragged_point_idx
    if dragged_point_idx is not None and points:
        turtle_x = event.x - (SCREEN_WIDTH / 2)
        turtle_y = (SCREEN_HEIGHT / 2) - event.y
        points[dragged_point_idx][0] = turtle_x
        points[dragged_point_idx][1] = turtle_y
        points[dragged_point_idx][2] = turtle_x


def on_release(event):
    global dragged_point_idx
    dragged_point_idx = None


# --- EVENT BINDINGS ---
screen.listen()
screen.onscreenclick(on_click)

canvas = screen.getcanvas()
canvas.bind("<B1-Motion>", on_drag_canvas)
canvas.bind("<ButtonRelease-1>", on_release)

# --- ENGINE ANIMATION LOOP ---


def main_loop():
    update_physics()
    render_scene()
    screen.ontimer(main_loop, 16)


main_loop()
turtle.done()
