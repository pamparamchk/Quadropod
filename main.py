import pygame
import sys
import math

pygame.init()
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("spider sim")
font = pygame.font.SysFont("Arial", 14)
font_bold = pygame.font.SysFont("Arial", 14, bold=True)
tooltip_font = pygame.font.SysFont("Arial", 12, bold=True)
clock = pygame.time.Clock()

app_state = "DESIGN"
interaction_mode = "VIEW"

gait_time = 0.0
gait_speed = 0.012
step_height = 2.5
stride_len = 3.5

angle_x, angle_y = -0.5, 0.6
cam_center_x, cam_center_y = 980, 350
zoom = 28.0

world_objects = [
    {"type": "Cube", "x": 0.0, "y": 0.0, "z": -4.0, "size": 4.0},
    {"type": "Sphere", "x": -6.0, "y": 0.0, "z": 4.0, "size": 3.0}
]
selected_obj_idx = -1

spawn_type_list = ["Cube", "Sphere"]
selected_spawn_type_idx = 0
dropdown_open = False

def project_3d(x, y, z):
    x1 = x * math.cos(angle_y) - z * math.sin(angle_y)
    z1 = x * math.sin(angle_y) + z * math.cos(angle_y)
    y2 = y * math.cos(angle_x) - z1 * math.sin(angle_x)
    z2 = y * math.sin(angle_x) + z1 * math.cos(angle_x)
    
    distance = 40.0
    scale = (zoom * 20.0) / (z2 + distance)
    return int(cam_center_x + x1 * scale), int(cam_center_y - y2 * scale)

def get_terrain_height(x, z):
    highest_y = 0.0
    for obj in world_objects:
        if obj["type"] == "Cube":
            half = obj["size"] / 2.0
            if (obj["x"] - half <= x <= obj["x"] + half) and (obj["z"] - half <= z <= obj["z"] + half):
                top_y = obj["y"] + half
                if top_y > highest_y:
                    highest_y = top_y
        elif obj["type"] == "Sphere":
            dx = x - obj["x"]
            dz = z - obj["z"]
            dist_2d = math.sqrt(dx*dx + dz*dz)
            if dist_2d < obj["size"]:
                arg = obj["size"]**2 - dist_2d**2
                top_y = obj["y"] + math.sqrt(max(0.0, arg))
                if top_y > highest_y:
                    highest_y = top_y
    return highest_y

GRID_ROWS, GRID_COLS = 40, 40  
CELL_SIZE = 11                 
GRID_OFFSET_X, GRID_OFFSET_Y = 300, 120
inventory_scroll_y = 0  

config = {
    "cm_per_cell": "1.0",      
    "part_name": "",           
    "part_weight": "1.5",      
    "part_height": "2.0",      
    "part_z_offset": "0.0",    
}
active_field = "part_weight"    
drawn_parts = []
drawing_start = None

PART_COLORS = [
    (140, 90, 180), (230, 126, 34), (46, 204, 113), 
    (241, 196, 15), (231, 76, 60), (26, 188, 156)
]

com_grid_x, com_grid_y, com_grid_z = 20.0, 20.0, 0.0
body_w, body_l = 12.0, 16.0      
body_h = 4      
stance_width = 4.5
step_reach = 1.5 

L_COXA, L_FEMUR, L_TIBIA = 3.0, 7.0, 9.0

def update_system_physics():
    global com_grid_x, com_grid_y, com_grid_z, body_w, body_l
    total_mass = 0.0
    sum_x, sum_y, sum_z = 0.0, 0.0, 0.0
    try: cell_scale = float(config["cm_per_cell"])
    except ValueError: cell_scale = 1.0

    if not drawn_parts:
        com_grid_x, com_grid_y, com_grid_z = 20.0, 20.0, 0.0
        body_w, body_l = 12.0, 16.0
        return

    min_x, max_x = 999.0, -999.0
    min_y, max_y = 999.0, -999.0

    for idx, part in enumerate(drawn_parts):
        r = part["rect"]
        w = part["weight"]
        if r.x < min_x: min_x = r.x
        if r.x + r.width > max_x: max_x = r.x + r.width
        if r.y < min_y: min_y = r.y
        if r.y + r.height > max_y: max_y = r.y + r.height

        cx, cy = r.x + r.width / 2.0, r.y + r.height / 2.0
        if idx == 0:
            actual_z = part["z_offset"]
        else:
            main_body = drawn_parts[0]
            main_top_face = main_body["z_offset"] + (main_body["height"] / 2.0)
            actual_z = main_top_face + part["z_offset"] + (part["height"] / 2.0)
            
        cz = actual_z / cell_scale if cell_scale != 0 else actual_z
        sum_x += cx * w; sum_y += cy * w; sum_z += cz * w
        total_mass += w
        
    if total_mass > 0:
        com_grid_x, com_grid_y, com_grid_z = sum_x / total_mass, sum_y / total_mass, (sum_z / total_mass) * cell_scale
        body_w = (max_x - min_x) * cell_scale
        body_l = (max_y - min_y) * cell_scale

fields_registry = [
    ("cm_per_cell", "Grid Square Scale (cm):", 50),
    ("part_name", "Custom Part Name:", 110),
    ("part_weight", "Part Weight (g):", 150),
    ("part_height", "Part Height (cm):", 190),
    ("part_z_offset", "Part Z Offset (cm):", 230),
]

while True:
    screen.fill((16, 18, 22))
    keys = pygame.key.get_pressed()
    mx, my = pygame.mouse.get_pos()
    if interaction_mode != "GRAB":
        if keys[pygame.K_LEFT]:  angle_y -= 0.03
        if keys[pygame.K_RIGHT]: angle_y += 0.03
        if keys[pygame.K_UP]:    angle_x -= 0.03
        if keys[pygame.K_DOWN]:  angle_x += 0.03
        
        if keys[pygame.K_w]: body_h = min(14.0, body_h + 0.15)
        if keys[pygame.K_s]: body_h = max(2.0, body_h - 0.15)
        if keys[pygame.K_d]: stance_width = min(20.0, stance_width + 0.15)
        if keys[pygame.K_a]: stance_width = max(1.0, stance_width - 0.15)
        if keys[pygame.K_i]: step_reach = min(20.0, step_reach + 0.15)
        if keys[pygame.K_k]: step_reach = max(-10.0, step_reach - 0.15)
    else:
        if selected_obj_idx != -1:
            obj = world_objects[selected_obj_idx]
            if keys[pygame.K_w]: obj["z"] -= 0.15
            if keys[pygame.K_s]: obj["z"] += 0.15
            if keys[pygame.K_a]: obj["x"] -= 0.15
            if keys[pygame.K_d]: obj["x"] += 0.15
            if keys[pygame.K_i]: obj["y"] += 0.15
            if keys[pygame.K_k]: obj["y"] = max(-5.0, obj["y"] - 0.15)

    grid_mx = (mx - GRID_OFFSET_X) // CELL_SIZE
    grid_my = (my - GRID_OFFSET_Y) // CELL_SIZE

    if app_state == "DESIGN":
        cam_center_x, cam_center_y = 980, 350
    else:
        cam_center_x, cam_center_y = 600, 350
        gait_time = (gait_time + gait_speed) % 1.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                app_state = "SIMULATION" if app_state == "DESIGN" else "DESIGN"
                interaction_mode = "VIEW"
                
            if app_state == "SIMULATION":
                if event.key == pygame.K_s:
                    interaction_mode = "SELECT"
                elif event.key == pygame.K_g:
                    if selected_obj_idx != -1:
                        interaction_mode = "GRAB"
                elif event.key == pygame.K_e:
                    if selected_obj_idx != -1:
                        curr = world_objects[selected_obj_idx]["type"]
                        world_objects[selected_obj_idx]["type"] = "Sphere" if curr == "Cube" else "Cube"
                elif event.key == pygame.K_c:
                    t = spawn_type_list[selected_spawn_type_idx]
                    world_objects.append({"type": t, "x": 0.0, "y": 2.0, "z": 0.0, "size": 3.0})
                    selected_obj_idx = len(world_objects) - 1
                elif event.key == pygame.K_LEFTBRACKET:
                    if selected_obj_idx != -1:
                        world_objects[selected_obj_idx]["size"] = max(1.0, world_objects[selected_obj_idx]["size"] - 0.5)
                elif event.key == pygame.K_RIGHTBRACKET:
                    if selected_obj_idx != -1:
                        world_objects[selected_obj_idx]["size"] = min(15.0, world_objects[selected_obj_idx]["size"] + 0.5)
            
            if app_state == "DESIGN":
                if event.key == pygame.K_BACKSPACE:
                    config[active_field] = config[active_field][:-1]
                elif event.key == pygame.K_c and active_field != "part_name":
                    drawn_parts.clear()
                else:
                    if active_field == "part_name":
                        if len(config[active_field]) < 15 and (event.unicode.isalnum() or event.unicode == ' '):
                            config[active_field] += event.unicode
                    else:
                        if event.unicode in "0123456789.-":
                            config[active_field] += event.unicode
                
                update_system_physics()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if app_state == "SIMULATION":
                if 20 <= mx <= 160 and 80 <= my <= 105:
                    dropdown_open = not dropdown_open
                elif dropdown_open and 20 <= mx <= 160 and 105 <= my <= 105 + len(spawn_type_list)*22:
                    clicked_idx = (my - 105) // 22
                    if 0 <= clicked_idx < len(spawn_type_list):
                        selected_spawn_type_idx = clicked_idx
                    dropdown_open = False
                else:
                    dropdown_open = False
                
                if interaction_mode == "SELECT":
                    best_idx = -1
                    min_dist = 999999.0
                    for idx, obj in enumerate(world_objects):
                        sx, sy = project_3d(obj["x"], obj["y"], obj["z"])
                        dist = math.sqrt((mx - sx)**2 + (my - sy)**2)
                        if dist < 45.0 and dist < min_dist:
                            min_dist = dist
                            best_idx = idx
                    selected_obj_idx = best_idx
                    if selected_obj_idx != -1:
                        interaction_mode = "VIEW"

            elif app_state == "DESIGN" and event.button == 1:
                for field_id, _, y_pos in fields_registry:
                    if 20 <= mx <= 260 and y_pos <= my <= y_pos + 22: active_field = field_id
                if 0 <= grid_mx < GRID_COLS and 0 <= grid_my < GRID_ROWS: drawing_start = (grid_mx, grid_my)

        elif event.type == pygame.MOUSEBUTTONUP and app_state == "DESIGN" and event.button == 1:
            if drawing_start is not None:
                x1, y1 = drawing_start
                x2, y2 = max(0, min(grid_mx, GRID_COLS-1)), max(0, min(grid_my, GRID_ROWS-1))
                rx, ry = min(x1, x2), min(y1, y2)
                rw, rh = abs(x1 - x2) + 1, abs(y1 - y2) + 1
                try: w = float(config["part_weight"])
                except ValueError: w = 1.0
                try: h = float(config["part_height"])
                except ValueError: h = 1.0
                try: z_o = float(config["part_z_offset"])
                except ValueError: z_o = 0.0
                name = config["part_name"].strip() if config["part_name"].strip() else f"Module {len(drawn_parts)}"
                if len(drawn_parts) == 0: name = "Base Chassis Root"
                drawn_parts.append({"rect": pygame.Rect(rx, ry, rw, rh), "weight": w, "height": h, "z_offset": z_o, "name": name})
                update_system_physics()
                drawing_start = None

    if app_state == "DESIGN":
        pygame.draw.line(screen, (50, 50, 50), (280, 0), (280, HEIGHT), 2)
        pygame.draw.line(screen, (50, 50, 50), (760, 0), (760, HEIGHT), 2)
        screen.blit(font_bold.render("EDITOR", True, (100, 200, 255)), (20, 25))
        
        for field_id, label, y_pos in fields_registry:
            f_color = (255, 255, 255) if active_field == field_id else (150, 150, 150)
            box_color = (0, 150, 255) if active_field == field_id else (70, 70, 70)
            screen.blit(font.render(label, True, f_color), (20, y_pos))
            input_rect = pygame.Rect(170, y_pos - 3, 100, 20)
            pygame.draw.rect(screen, (30, 30, 30), input_rect)
            pygame.draw.rect(screen, box_color, input_rect, 1 if active_field != field_id else 2)
            screen.blit(font.render(config[field_id], True, (255, 255, 255)), (175, y_pos))

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = pygame.Rect(GRID_OFFSET_X + c * CELL_SIZE, GRID_OFFSET_Y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (32, 32, 32) if (r+c)%2==0 else (28, 28, 28), rect)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)

        for idx, part in enumerate(drawn_parts):
            pr = part["rect"]
            p_color = (52, 152, 219) if idx == 0 else PART_COLORS[(idx - 1) % len(PART_COLORS)]
            pygame.draw.rect(screen, p_color, (GRID_OFFSET_X + pr.x*CELL_SIZE, GRID_OFFSET_Y + pr.y*CELL_SIZE, pr.width*CELL_SIZE, pr.height*CELL_SIZE))

    for idx, obj in enumerate(world_objects):
        is_sel = (idx == selected_obj_idx)
        base_color = (230, 126, 34) if obj["type"] == "Cube" else (155, 89, 182)
        color = (255, 230, 100) if (is_sel and interaction_mode == "GRAB") else (base_color if not is_sel else (255, 255, 255))
        
        if obj["type"] == "Cube":
            h = obj["size"] / 2.0
            v0 = project_3d(obj["x"]-h, obj["y"]+h, obj["z"]-h)
            v1 = project_3d(obj["x"]+h, obj["y"]+h, obj["z"]-h)
            v2 = project_3d(obj["x"]+h, obj["y"]+h, obj["z"]+h)
            v3 = project_3d(obj["x"]-h, obj["y"]+h, obj["z"]+h)
            v4 = project_3d(obj["x"]-h, obj["y"]-h, obj["z"]-h)
            v5 = project_3d(obj["x"]+h, obj["y"]-h, obj["z"]-h)
            v6 = project_3d(obj["x"]+h, obj["y"]-h, obj["z"]+h)
            v7 = project_3d(obj["x"]-h, obj["y"]-h, obj["z"]+h)
            
            for p1, p2 in [(v0,v1),(v1,v2),(v2,v3),(v3,v0),(v4,v5),(v5,v6),(v6,v7),(v7,v4),(v0,v4),(v1,v5),(v2,v6),(v3,v7)]:
                pygame.draw.line(screen, color, p1, p2, 2 if is_sel else 1)
        
        elif obj["type"] == "Sphere":
            cx, cy = project_3d(obj["x"], obj["y"], obj["z"])
            rad_3d = int(obj["size"] * (zoom * 20.0) / (obj["z"] + 40.0))
            if rad_3d > 0:
                pygame.draw.circle(screen, color, (cx, cy), rad_3d, 2 if is_sel else 1)

    parts_to_render = drawn_parts if drawn_parts else [{"rect": pygame.Rect(12, 14, 16, 12), "weight": 1.0, "height": 2.0, "z_offset": 0.0, "name": "Chassis"}]
    try: scale_cm = max(0.1, float(config["cm_per_cell"]))
    except ValueError: scale_cm = 1.0

    main_body_z_center = (parts_to_render[0]["z_offset"] / scale_cm) * 0.4
    main_body_half_h = (((parts_to_render[0]["height"]) / scale_cm) / 2.0) * 0.4
    main_body_top_face_y = main_body_z_center + main_body_half_h

    for idx, part in enumerate(parts_to_render):
        r = part["rect"]
        p_color = (52, 152, 219) if (drawn_parts and idx == 0) else ((100,100,100) if not drawn_parts else PART_COLORS[(idx - 1) % len(PART_COLORS)])
        x_min, x_max = (r.x - 20) * 0.4, (r.x + r.width - 20) * 0.4
        z_min, z_max = (r.y - 20) * 0.4, (r.y + r.height - 20) * 0.4
        
        y_thick = ((part["height"] / scale_cm) / 2.0) * 0.4
        y_center = main_body_z_center + y_thick if idx == 0 else main_body_top_face_y + ((part["z_offset"] / scale_cm) * 0.4) + y_thick
        y_top, y_bottom = body_h + (y_center + y_thick), body_h + (y_center - y_thick)

        c1, c2 = project_3d(x_min, y_top, z_min), project_3d(x_max, y_top, z_min)
        c3, c4 = project_3d(x_max, y_top, z_max), project_3d(x_min, y_top, z_max)
        c5, c6 = project_3d(x_min, y_bottom, z_min), project_3d(x_max, y_bottom, z_min)
        c7, c8 = project_3d(x_max, y_bottom, z_max), project_3d(x_min, y_bottom, z_max)
        
        for pair in [(c1,c2), (c2,c3), (c3,c4), (c4,c1), (c5,c6), (c6,c7), (c7,c8), (c8,c5), (c1,c5), (c2,c6), (c3,c7), (c4,c8)]:
            pygame.draw.line(screen, p_color, pair[0], pair[1], 1)

    r_base = parts_to_render[0]["rect"]
    bx_min, bx_max = (r_base.x - 20) * 0.4, (r_base.x + r_base.width - 20) * 0.4
    bz_min, bz_max = (r_base.y - 20) * 0.4, (r_base.y + r_base.height - 20) * 0.4

    legs = [
        (bx_min, bz_min, -1, -1, 0.0),   # FL
        (bx_min, bz_max, -1,  1, 0.25),  # BL
        (bx_max, bz_max,  1,  1, 0.5),   # BR
        (bx_max, bz_min,  1, -1, 0.75)   # FR
    ]

    for hip_x, hip_z, dir_x, dir_z, phase_offset in legs:
        p_hip = project_3d(hip_x, body_h, hip_z)
        leg_phase = (gait_time + phase_offset) % 1.0
        neutral_x = hip_x + (dir_x * stance_width)
        neutral_z = hip_z + (dir_z * step_reach)
        
        z_start = neutral_z + stride_len
        z_end = neutral_z - stride_len

        if app_state == "SIMULATION":
            if leg_phase < 0.25:
                t_swing = leg_phase / 0.25 
                foot_x = neutral_x
                foot_z = (1 - t_swing)**2 * z_start + 2 * (1 - t_swing) * t_swing * ((z_start + z_end)/2.0) + t_swing**2 * z_end
                
                t_ground = get_terrain_height(foot_x, foot_z)
                arc_y = 4.0 * step_height * t_swing * (1 - t_swing)
                foot_y = t_ground + arc_y
            else:
                t_stance = (leg_phase - 0.25) / 0.75 
                foot_x = neutral_x
                foot_z = z_end + (z_start - z_end) * t_stance
                foot_y = get_terrain_height(foot_x, foot_z)
        else:
            foot_x, foot_y, foot_z = neutral_x, get_terrain_height(neutral_x, neutral_z), neutral_z

        p_foot = project_3d(foot_x, foot_y, foot_z)
        
        dx, dz = foot_x - hip_x, foot_z - hip_z
        leg_heading = math.atan2(dz, dx)
        l_coxa, l_femur, l_tibia = L_COXA * 0.4, L_FEMUR * 0.4, L_TIBIA * 0.4

        thigh_x = hip_x + l_coxa * math.cos(leg_heading)
        thigh_z = hip_z + l_coxa * math.sin(leg_heading)
        thigh_y = body_h
        p_thigh = project_3d(thigh_x, thigh_y, thigh_z)
        
        rem_x, rem_z = foot_x - thigh_x, foot_z - thigh_z
        horizontal_dist = math.sqrt(rem_x**2 + rem_z**2)
        vertical_dist = foot_y - thigh_y
        
        R = math.sqrt(horizontal_dist**2 + vertical_dist**2)
        max_reach = l_femur + l_tibia - 0.001
        
        if R > max_reach:
            scale = max_reach / R
            horizontal_dist *= scale; vertical_dist *= scale; R = max_reach
            foot_x = thigh_x + horizontal_dist * math.cos(leg_heading)
            foot_z = thigh_z + horizontal_dist * math.sin(leg_heading)
            foot_y = thigh_y + vertical_dist
            p_foot = project_3d(foot_x, foot_y, foot_z)

        angle_target = math.atan2(vertical_dist, horizontal_dist)
        cos_alpha = (l_femur**2 + R**2 - l_tibia**2) / (2 * l_femur * R)
        alpha = math.acos(max(-1.0, min(1.0, cos_alpha)))
        
        angle_femur = angle_target + alpha
        knee_dist = l_femur * math.cos(angle_femur)
        knee_y = thigh_y + l_femur * math.sin(angle_femur)
        knee_x = thigh_x + knee_dist * math.cos(leg_heading)
        knee_z = thigh_z + knee_dist * math.sin(leg_heading)
        p_knee = project_3d(knee_x, knee_y, knee_z)

        bone_color = (231, 76, 60) if (app_state == "SIMULATION" and leg_phase < 0.25) else (50, 210, 110)
        pygame.draw.line(screen, (240, 130, 40), p_hip, p_thigh, 4)
        pygame.draw.line(screen, bone_color, p_thigh, p_knee, 4)
        pygame.draw.line(screen, (255, 210, 60), p_knee, p_foot, 3)
        pygame.draw.circle(screen, (255, 60, 60), p_foot, 5)

    mode_color = (0, 160, 255) if app_state == "DESIGN" else (46, 204, 113)
    pygame.draw.rect(screen, mode_color, (450, 15, 300, 24), 0, 4)
    screen.blit(font_bold.render(f"Mode: {app_state} (Press TAB)", True, (255, 255, 255)), (465, 20))

    if app_state == "SIMULATION":
        pygame.draw.rect(screen, (30, 30, 40), (20, 80, 140, 25), 0, 3)
        pygame.draw.rect(screen, (70, 70, 90), (20, 80, 140, 25), 1)
        screen.blit(font.render(f"Create: {spawn_type_list[selected_spawn_type_idx]}", True, (255, 255, 255)), (28, 84))
        pygame.draw.polygon(screen, (200, 200, 200), [(142, 89), (150, 89), (146, 96)])
        
        if dropdown_open:
            for idx, item in enumerate(spawn_type_list):
                dy = 105 + idx * 22
                pygame.draw.rect(screen, (20, 20, 30), (20, dy, 140, 22))
                pygame.draw.rect(screen, (50, 50, 70), (20, dy, 140, 22), 1)
                screen.blit(font.render(item, True, (200, 200, 200)), (28, dy + 3))

        screen.blit(font_bold.render("CONTROLS", True, (255, 255, 255)), (20, 460))
        screen.blit(font.render("C - Create Object", True, (241, 196, 15)), (20, 485))
        screen.blit(font.render("S - Select Mode", True, (46, 204, 113)), (20, 505))
        screen.blit(font.render("G - Grab Mode", True, (52, 152, 219)), (20, 525))
        screen.blit(font.render("E - Toggle Object Type", True, (200, 200, 200)), (20, 545))
        screen.blit(font.render("[ / ] - Alter object size", True, (200, 200, 200)), (20, 565))
        
        if selected_obj_idx != -1 and selected_obj_idx < len(world_objects):
            o = world_objects[selected_obj_idx]
            screen.blit(font_bold.render(f"Target Inspector ({o['type']})", True, (255, 100, 255)), (20, 600))
            screen.blit(font.render(f"Coordinates: X:{o['x']:.1f} Y:{o['y']:.1f} Z:{o['z']:.1f}", True, (255, 255, 255)), (20, 620))
            screen.blit(font.render(f"DScale: {o['size']:.1f} cm", True, (255, 255, 255)), (20, 640))

    pygame.display.flip()
    clock.tick(60)