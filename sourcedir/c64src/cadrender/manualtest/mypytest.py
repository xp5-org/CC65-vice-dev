import pygame
import math
import sys
import re

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

angle_x = 0.0
angle_y = 0.0
zoom = 5.0
dragging = False
last_mouse = (0, 0)

def parse_c_arrays(filename):
    with open(filename, "r") as f:
        text = f.read()

    # Remove C-style comments
    text = re.sub(r"//.*", "", text)

    # Match Point3D arrays (allow numbers or identifiers in brackets)
    points_arrays = {}
    for match in re.finditer(r"Point3D\s+(\w+)\s*\[[^\]]+\]\s*=\s*\{(.*?)\};", text, re.S):
        name, body = match.groups()
        pts = []
        for triplet in re.findall(r"\{([^{}]+)\}", body):
            nums = [float(x) for x in triplet.split(",")]
            pts.append(nums)
        points_arrays[name] = pts

    # Match FaceTri arrays (allow numbers or identifiers in brackets)
    tris_arrays = {}
    for match in re.finditer(r"FaceTri\s+(\w+)\s*\[[^\]]+\]\s*=\s*\{(.*?)\};", text, re.S):
        name, body = match.groups()
        tris = []
        for triplet in re.findall(r"\{([^{}]+)\}", body):
            nums = [int(x) for x in triplet.split(",")]
            tris.append(nums)
        tris_arrays[name] = tris

    return points_arrays, tris_arrays




points_dict, tris_dict = parse_c_arrays("object.txt")




if not points_dict or not tris_dict:
    print("No objects found in file!")
    pygame.quit()
    sys.exit()

# pick the first object dynamically
points = next(iter(points_dict.values()))
tris = next(iter(tris_dict.values()))


def rotate_point(px, py, pz, ax, ay):
    cosx, sinx = math.cos(ax), math.sin(ax)
    cosy, siny = math.cos(ay), math.sin(ay)
    y = py * cosx - pz * sinx
    z = py * sinx + pz * cosx
    x = px
    x2 = x * cosy + z * siny
    z2 = -x * siny + z * cosy
    y2 = y
    return [x2, y2, z2]

def project_point(p):
    scale = zoom
    x = WIDTH//2 + int(p[0]*scale)
    y = HEIGHT//2 - int(p[1]*scale)
    return (x, y)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                last_mouse = event.pos
            elif event.button == 4:
                zoom *= 1.1
            elif event.button == 5:
                zoom /= 1.1
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            dx = event.pos[0] - last_mouse[0]
            dy = event.pos[1] - last_mouse[1]
            angle_y += dx * 0.01
            angle_x += dy * 0.01
            last_mouse = event.pos

    screen.fill((30, 30, 30))
    transformed = [rotate_point(*p, angle_x, angle_y) for p in points]
    projected = [project_point(p) for p in transformed]

    for tri in tris:
        pygame.draw.polygon(screen, (200, 200, 200),
                            [projected[tri[0]], projected[tri[1]], projected[tri[2]]], 1)

    pygame.display.flip()
    clock.tick(60)
