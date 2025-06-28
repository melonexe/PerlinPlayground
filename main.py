import pygame
import random
import math
import noise
import colorsys

# Settings
WIDTH, HEIGHT = 2560, 1440
PARTICLE_COUNT = 1000
SPEED = 3.0
NOISE_SCALE = 0.002
PARTICLE_SIZE = 3

# Particle class
class Particle:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = 0.0
        self.vy = 0.0
        self.color = (255, 0, 0)
        self.angle_deg = 0

    # Update Particle.update to use LFO
    def update(self, t, flip_dim=False, speed=3.0, steering_strength=0.01, lfo_enabled=False, lfo_amplitude=0.0, lfo_rate=0.0, waveform=0, particles=None, particle_size=1, grid=None, grid_size=None):
        # LFO value with waveform selection
        lfo_val = 0.0
        if lfo_enabled and lfo_rate > 0:
            phase = t * lfo_rate
            if waveform == 0:  # Sine
                lfo_val = lfo_amplitude * math.sin(phase * 2 * math.pi)
            elif waveform == 1:  # Square
                lfo_val = lfo_amplitude * (1 if math.sin(phase * 2 * math.pi) >= 0 else -1)
            elif waveform == 2:  # Triangle
                lfo_val = lfo_amplitude * (2 * abs(2 * (phase % 1) - 1) - 1)
            elif waveform == 3:  # Saw
                lfo_val = lfo_amplitude * (2 * (phase % 1) - 1)
        if not flip_dim:
            angle = noise.pnoise3((self.x + lfo_val) * NOISE_SCALE, self.y * NOISE_SCALE, t) * 2 * math.pi
        else:
            angle = noise.pnoise3(self.y * NOISE_SCALE, (self.x + lfo_val) * NOISE_SCALE, t) * 2 * math.pi
        target_vx = math.cos(angle) * speed
        target_vy = math.sin(angle) * speed
        self.vx += (target_vx - self.vx) * steering_strength
        self.vy += (target_vy - self.vy) * steering_strength
        self.x += self.vx
        self.y += self.vy
        self.angle_deg = (math.degrees(angle) + 360) % 360
        if self.x < 0: self.x += WIDTH
        if self.x > WIDTH: self.x -= WIDTH
        if self.y < 0: self.y += HEIGHT
        if self.y > HEIGHT: self.y -= HEIGHT

    def draw(self, surface, color_start_hue=0.0, color_end_hue=240.0, particle_size=3, particle_shape=0, color_directional=True, rgb_values=None, idx=0, total=1):
        if color_directional:
            rel = self.angle_deg / 360.0
            hue1 = color_start_hue / 360.0
            hue2 = color_end_hue / 360.0
            if abs(hue2 - hue1) > 0.5:
                if hue1 > hue2:
                    hue2 += 1.0
                else:
                    hue1 += 1.0
            hue = (hue1 + (hue2 - hue1) * rel) % 1.0
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
            self.color = (int(r * 255), int(g * 255), int(b * 255))
        else:
            if rgb_values is not None:
                # Interpolate between start and end RGB based on particle index
                rel = idx / max(total-1, 1)
                r = int(rgb_values[0] + (rgb_values[3] - rgb_values[0]) * rel)
                g = int(rgb_values[1] + (rgb_values[4] - rgb_values[1]) * rel)
                b = int(rgb_values[2] + (rgb_values[5] - rgb_values[2]) * rel)
                self.color = (r, g, b)
            else:
                self.color = (255, 255, 255)
        if particle_shape == 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), particle_size)
        else:
            pygame.draw.rect(surface, self.color, (int(self.x)-particle_size, int(self.y)-particle_size, 2*particle_size, 2*particle_size))

def draw_button(surface, rect, text, color, text_color=(255,255,255)):
    pygame.draw.rect(surface, color, rect)
    font = pygame.font.SysFont(None, 36)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def draw_slider(surface, rect, min_val, max_val, value, color, handle_color, label=None):
    pygame.draw.rect(surface, color, rect, border_radius=5)
    handle_x = rect.x + int((value - min_val) / (max_val - min_val) * rect.width)
    handle_rect = pygame.Rect(handle_x - 8, rect.centery - 12, 16, 24)
    pygame.draw.rect(surface, handle_color, handle_rect, border_radius=6)
    font = pygame.font.SysFont(None, 28)
    if label:
        val_surf = font.render(f"{label}: {value:.3f}", True, (255,255,255))
    else:
        val_surf = font.render(f"{value:.3f}", True, (255,255,255))
    surface.blit(val_surf, (rect.x + rect.width + 20, rect.y + rect.height//2 - 14))
    return handle_rect

def draw_toggle(surface, rect, state, label):
    pygame.draw.rect(surface, (80, 80, 80), rect, border_radius=12)
    knob_rect = pygame.Rect(rect.x + (rect.width//2 if state else 0), rect.y, rect.width//2, rect.height)
    pygame.draw.rect(surface, (0,200,0) if state else (200,0,0), knob_rect, border_radius=12)
    font = pygame.font.SysFont(None, 28)
    label_surf = font.render(label, True, (255,255,255))
    surface.blit(label_surf, (rect.x + rect.width + 10, rect.y + rect.height//2 - 14))
    return knob_rect

def draw_density_background(surface, particles, grid_size=32):
    cols = WIDTH // grid_size + 1
    rows = HEIGHT // grid_size + 1
    density = [[0 for _ in range(cols)] for _ in range(rows)]
    for p in particles:
        col = int(p.x // grid_size)
        row = int(p.y // grid_size)
        if 0 <= col < cols and 0 <= row < rows:
            density[row][col] += 1
    max_density = max(max(row) for row in density) or 1
    # Use a temporary surface for alpha blending
    bg_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for row in range(rows):
        for col in range(cols):
            d = density[row][col]
            hue = (0.6 - 0.6 * (d / max_density)) % 1.0
            brightness = 0.2 + 0.8 * (d / max_density)
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, 1, brightness)
            alpha = int(80 + 175 * (d / max_density))  # More density, more opaque
            color = (int(r*255), int(g*255), int(b*255), alpha)
            pygame.draw.rect(bg_surf, color, (col*grid_size, row*grid_size, grid_size, grid_size))
    surface.blit(bg_surf, (0, 0))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Perlin Noise Particle Simulation")
    clock = pygame.time.Clock()

    particles = [Particle() for _ in range(PARTICLE_COUNT)]
    t = 0

    # Store default values for reset (restored)
    default_params = dict(
        speed=3.0,
        steering_strength=0.01,
        res_grid_size=32,
        show_density_bg=False,
        menu_collapsed=False,
        color_start_hue=0.0,
        color_end_hue=240.0,
        particle_size=1,
        particle_shape=0,
        color_directional=False,
        lfo_enabled=False,
        lfo_amplitude=0.0,
        lfo_rate=0.0,
        waveform=0,
        rgb_values=[255, 0, 0, 0, 0, 255]
    )

    # Initialize all UI state variables at the start
    speed = 3.0
    steering_strength = 0.01
    res_grid_size = 32
    show_density_bg = True
    menu_collapsed = False
    color_start_hue = 0.0
    color_end_hue = 240.0
    particle_size = 3
    particle_shape = 0
    color_directional = True

    # Menu layout
    menu_width = 600  # Increased from 340 for a much wider menu area
    menu_collapsed = False
    tab_rect = pygame.Rect(0, 0, 80, 80)  # Increased width from 32 to 80 for a wider tab
    menu_bg_color = (30, 30, 30)
    menu_x = 0
    menu_y = 0
    menu_spacing = 20
    btn_h = 50
    slider_h = 20
    toggle_h = 32
    ui_y = menu_y + menu_spacing
    # UI element rects (vertical stack)
    add_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    remove_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    flip_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    randomise_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    speed_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    steering_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    res_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    toggle_rect = pygame.Rect(menu_x + 20, ui_y, 60, toggle_h)
    ui_y += toggle_h + menu_spacing
    color_start_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    color_end_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    particle_size_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    particle_shape_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    color_dir_toggle_rect = pygame.Rect(menu_x + 20, ui_y, 60, toggle_h)
    ui_y += toggle_h + menu_spacing
    counter_y = ui_y

    # Add LFO controls
    lfo_toggle_rect = pygame.Rect(menu_x + 20, ui_y, 60, toggle_h)
    ui_y += toggle_h + menu_spacing
    lfo_amp_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    lfo_rate_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    # Add waveform selection slider
    waveform_slider_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
    ui_y += slider_h + menu_spacing
    waveform = 0  # 0=sine, 1=square, 2=triangle, 3=saw
    dragging_lfo_amp_slider = False
    dragging_lfo_rate_slider = False
    dragging_waveform_slider = False
    waveform_names = ['Sine', 'Square', 'Triangle', 'Saw']

    lfo_enabled = False
    lfo_amplitude = 0.0
    lfo_rate = 0.0
    LFO_AMP_MIN = 0.0
    LFO_AMP_MAX = 500.0
    LFO_RATE_MIN = 0.0
    LFO_RATE_MAX = 2.0

    # Slider limits
    SPEED_MIN = 0.1
    SPEED_MAX = 10.0
    STEERING_MIN = 0.001
    STEERING_MAX = 0.2
    res_min = 2  # Lower minimum grid size for finer gradients
    res_max = 128
    res_grid_size = 32
    PARTICLE_SIZE_MIN = 1
    PARTICLE_SIZE_MAX = 10
    particle_size = 1

    # Colors
    btn_color = (50, 50, 50)
    btn_hover = (100, 0, 0)
    slider_color = (80, 80, 80)
    handle_color = (200, 0, 0)

    # States
    dragging_speed_slider = False
    dragging_steering_slider = False
    dragging_res_slider = False
    dragging_color_start_slider = False
    dragging_color_end_slider = False
    dragging_particle_size_slider = False
    dragging_particle_shape_slider = False
    dragging_lfo_amp_slider = False
    dragging_lfo_rate_slider = False
    dragging_waveform_slider = False
    dragging_rgb_sliders = [False] * 6
    flip_dim = False
    show_density_bg = True

    # Add RGB sliders for color range (when not in direction mode)
    rgb_slider_labels = ["Start R", "Start G", "Start B", "End R", "End G", "End B"]
    rgb_slider_rects = []
    rgb_values = [255, 0, 0, 0, 0, 255]  # Default: red to blue
    RGB_MIN = 0
    RGB_MAX = 255
    dragging_rgb_sliders = [False] * 6
    for i in range(6):
        rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, slider_h)
        rgb_slider_rects.append(rect)
        ui_y += slider_h + menu_spacing

    # Add reset and exit buttons
    reset_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    exit_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing

    # Add randomise sliders button
    randomise_sliders_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing

    # Add pause button
    pause_btn_rect = pygame.Rect(menu_x + 20, ui_y, menu_width - 40, btn_h)
    ui_y += btn_h + menu_spacing
    paused = False

    # Set BG and color dir toggles off by default
    show_density_bg = False
    color_directional = False

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        # Pre-calculate handle rects for all sliders and toggles
        speed_handle_rect = draw_slider(screen, speed_slider_rect, SPEED_MIN, SPEED_MAX, speed, slider_color, handle_color, label="Speed")
        steering_handle_rect = draw_slider(screen, steering_slider_rect, STEERING_MIN, STEERING_MAX, steering_strength, slider_color, handle_color, label="Steering")
        res_handle_rect = draw_slider(screen, res_slider_rect, res_min, res_max, res_grid_size, slider_color, handle_color, label="BG Res")
        color_start_handle_rect = draw_slider(screen, color_start_slider_rect, 0, 360, color_start_hue, slider_color, handle_color, label="Color Start")
        color_end_handle_rect = draw_slider(screen, color_end_slider_rect, 0, 360, color_end_hue, slider_color, handle_color, label="Color End")
        size_handle_rect = draw_slider(screen, particle_size_slider_rect, PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX, particle_size, slider_color, handle_color, label="Particle Size")
        shape_handle_rect = draw_slider(screen, particle_shape_slider_rect, 0, 1, particle_shape, slider_color, handle_color, label="Shape (0=Circle, 1=Square)")
        lfo_amp_handle_rect = draw_slider(screen, lfo_amp_slider_rect, LFO_AMP_MIN, LFO_AMP_MAX, lfo_amplitude, slider_color, handle_color, label="LFO Amp")
        lfo_rate_handle_rect = draw_slider(screen, lfo_rate_slider_rect, LFO_RATE_MIN, LFO_RATE_MAX, lfo_rate, slider_color, handle_color, label="LFO Rate")
        waveform_handle_rect = draw_slider(screen, waveform_slider_rect, 0, 3, waveform, slider_color, handle_color, label=f"Waveform: {waveform_names[int(waveform)]}")
        # Toggles
        toggle_knob_rect = draw_toggle(screen, toggle_rect, show_density_bg, "BG On")
        color_dir_toggle_knob_rect = draw_toggle(screen, color_dir_toggle_rect, color_directional, "Dir Color")
        lfo_toggle_knob_rect = draw_toggle(screen, lfo_toggle_rect, lfo_enabled, "LFO On")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if speed_handle_rect.collidepoint(mouse_pos) or speed_slider_rect.collidepoint(mouse_pos):
                    dragging_speed_slider = True
                if steering_handle_rect.collidepoint(mouse_pos) or steering_slider_rect.collidepoint(mouse_pos):
                    dragging_steering_slider = True
                if res_handle_rect.collidepoint(mouse_pos) or res_slider_rect.collidepoint(mouse_pos):
                    dragging_res_slider = True
                if color_start_handle_rect.collidepoint(mouse_pos) or color_start_slider_rect.collidepoint(mouse_pos):
                    dragging_color_start_slider = True
                if color_end_handle_rect.collidepoint(mouse_pos) or color_end_slider_rect.collidepoint(mouse_pos):
                    dragging_color_end_slider = True
                if size_handle_rect.collidepoint(mouse_pos) or particle_size_slider_rect.collidepoint(mouse_pos):
                    dragging_particle_size_slider = True
                if shape_handle_rect.collidepoint(mouse_pos) or particle_shape_slider_rect.collidepoint(mouse_pos):
                    dragging_particle_shape_slider = True
                if lfo_amp_handle_rect.collidepoint(mouse_pos) or lfo_amp_slider_rect.collidepoint(mouse_pos):
                    dragging_lfo_amp_slider = True
                if lfo_rate_handle_rect.collidepoint(mouse_pos) or lfo_rate_slider_rect.collidepoint(mouse_pos):
                    dragging_lfo_rate_slider = True
                if waveform_handle_rect.collidepoint(mouse_pos) or waveform_slider_rect.collidepoint(mouse_pos):
                    dragging_waveform_slider = True
                if toggle_knob_rect.collidepoint(mouse_pos) or toggle_rect.collidepoint(mouse_pos):
                    show_density_bg = not show_density_bg
                if color_dir_toggle_knob_rect.collidepoint(mouse_pos) or color_dir_toggle_rect.collidepoint(mouse_pos):
                    color_directional = not color_directional
                if lfo_toggle_knob_rect.collidepoint(mouse_pos) or lfo_toggle_rect.collidepoint(mouse_pos):
                    lfo_enabled = not lfo_enabled
                if tab_rect.collidepoint(mouse_pos):
                    menu_collapsed = not menu_collapsed
                if not menu_collapsed:
                    if add_btn_rect.collidepoint(mouse_pos):
                        for _ in range(1000):
                            particles.append(Particle())
                    if remove_btn_rect.collidepoint(mouse_pos):
                        for _ in range(1000):
                            if particles:
                                particles.pop()
                    if flip_btn_rect.collidepoint(mouse_pos):
                        flip_dim = not flip_dim
                    if randomise_btn_rect.collidepoint(mouse_pos):
                        for p in particles:
                            p.x = random.uniform(0, WIDTH)
                            p.y = random.uniform(0, HEIGHT)
                            p.vx = 0.0
                            p.vy = 0.0
                    if pause_btn_rect.collidepoint(mouse_pos):
                        paused = not paused
                # Reset button
                if reset_btn_rect.collidepoint(mouse_pos):
                    speed = default_params['speed']
                    steering_strength = default_params['steering_strength']
                    res_grid_size = default_params['res_grid_size']
                    show_density_bg = default_params['show_density_bg']
                    menu_collapsed = default_params['menu_collapsed']
                    color_start_hue = default_params['color_start_hue']
                    color_end_hue = default_params['color_end_hue']
                    particle_size = default_params['particle_size']
                    particle_shape = default_params['particle_shape']
                    color_directional = default_params['color_directional']
                    lfo_enabled = default_params['lfo_enabled']
                    lfo_amplitude = default_params['lfo_amplitude']
                    lfo_rate = default_params['lfo_rate']
                    waveform = default_params['waveform']
                    rgb_values = default_params['rgb_values'][:]
                # Exit button
                if exit_btn_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    return
                # Randomise sliders button
                if randomise_sliders_btn_rect.collidepoint(mouse_pos):
                    # import random  # Removed to avoid UnboundLocalError, use global import
                    speed = random.uniform(SPEED_MIN, SPEED_MAX)
                    steering_strength = random.uniform(STEERING_MIN, STEERING_MAX)
                    res_grid_size = random.randint(res_min, res_max)
                    color_start_hue = random.uniform(0, 360)
                    color_end_hue = random.uniform(0, 360)
                    # particle_size is NOT randomised
                    particle_shape = random.randint(0, 1)
                    lfo_amplitude = random.uniform(LFO_AMP_MIN, LFO_AMP_MAX)
                    lfo_rate = random.uniform(LFO_RATE_MIN, LFO_RATE_MAX)
                    waveform = random.randint(0, 3)
                    for i in range(6):
                        rgb_values[i] = random.randint(RGB_MIN, RGB_MAX)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_speed_slider = False
                dragging_steering_slider = False
                dragging_res_slider = False
                dragging_color_start_slider = False
                dragging_color_end_slider = False
                dragging_particle_size_slider = False
                dragging_particle_shape_slider = False
                dragging_lfo_amp_slider = False
                dragging_lfo_rate_slider = False
                dragging_waveform_slider = False
                for i in range(6):
                    dragging_rgb_sliders[i] = False
            for i, rect in enumerate(rgb_slider_rects):
                handle_rect = draw_slider(screen, rect, RGB_MIN, RGB_MAX, rgb_values[i], slider_color, handle_color, label=rgb_slider_labels[i])
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if handle_rect.collidepoint(mouse_pos) or rect.collidepoint(mouse_pos):
                        dragging_rgb_sliders[i] = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_rgb_sliders[i] = False
                if dragging_rgb_sliders[i]:
                    rel_x = min(max(mouse_pos[0] - rect.x, 0), rect.width)
                    rgb_values[i] = int(RGB_MIN + (RGB_MAX - RGB_MIN) * (rel_x / rect.width))
        if dragging_speed_slider:
            rel_x = min(max(mouse_pos[0] - speed_slider_rect.x, 0), speed_slider_rect.width)
            speed = SPEED_MIN + (SPEED_MAX - SPEED_MIN) * (rel_x / speed_slider_rect.width)
        if dragging_steering_slider:
            rel_x = min(max(mouse_pos[0] - steering_slider_rect.x, 0), steering_slider_rect.width)
            steering_strength = STEERING_MIN + (STEERING_MAX - STEERING_MIN) * (rel_x / steering_slider_rect.width)
        if dragging_res_slider:
            rel_x = min(max(mouse_pos[0] - res_slider_rect.x, 0), res_slider_rect.width)
            res_grid_size = int(res_min + (res_max - res_min) * (rel_x / res_slider_rect.width))
        if dragging_color_start_slider:
            rel_x = min(max(mouse_pos[0] - color_start_slider_rect.x, 0), color_start_slider_rect.width)
            color_start_hue = 0 + 360 * (rel_x / color_start_slider_rect.width)
        if dragging_color_end_slider:
            rel_x = min(max(mouse_pos[0] - color_end_slider_rect.x, 0), color_end_slider_rect.width)
            color_end_hue = 0 + 360 * (rel_x / color_end_slider_rect.width)
        if dragging_particle_size_slider:
            rel_x = min(max(mouse_pos[0] - particle_size_slider_rect.x, 0), particle_size_slider_rect.width)
            particle_size = max(1, int(PARTICLE_SIZE_MIN + (PARTICLE_SIZE_MAX - PARTICLE_SIZE_MIN) * (rel_x / particle_size_slider_rect.width)))
        if dragging_particle_shape_slider:
            rel_x = min(max(mouse_pos[0] - particle_shape_slider_rect.x, 0), particle_shape_slider_rect.width)
            particle_shape = 1 if rel_x > (particle_shape_slider_rect.width // 2) else 0
        if dragging_lfo_amp_slider:
            rel_x = min(max(mouse_pos[0] - lfo_amp_slider_rect.x, 0), lfo_amp_slider_rect.width)
            lfo_amplitude = LFO_AMP_MIN + (LFO_AMP_MAX - LFO_AMP_MIN) * (rel_x / lfo_amp_slider_rect.width)
        if dragging_lfo_rate_slider:
            rel_x = min(max(mouse_pos[0] - lfo_rate_slider_rect.x, 0), lfo_rate_slider_rect.width)
            lfo_rate = LFO_RATE_MIN + (LFO_RATE_MAX - LFO_RATE_MIN) * (rel_x / lfo_rate_slider_rect.width)
        if dragging_waveform_slider:
            rel_x = min(max(mouse_pos[0] - waveform_slider_rect.x, 0), waveform_slider_rect.width)
            waveform = int(0 + 3 * (rel_x / waveform_slider_rect.width) + 0.5)
            waveform = max(0, min(3, waveform))
        for i, rect in enumerate(rgb_slider_rects):
            if dragging_rgb_sliders[i]:
                rel_x = min(max(mouse_pos[0] - rect.x, 0), rect.width)
                rgb_values[i] = int(RGB_MIN + (RGB_MAX - RGB_MIN) * (rel_x / rect.width))

        # Draw background if enabled, else clear screen
        if show_density_bg:
            draw_density_background(screen, particles, grid_size=res_grid_size)
        else:
            screen.fill((0, 0, 0))
        # Draw menu background if open
        if not menu_collapsed:
            pygame.draw.rect(screen, menu_bg_color, (menu_x, menu_y, menu_width, HEIGHT))
        # Draw tab (always visible)
        pygame.draw.rect(screen, (60, 60, 60), tab_rect, border_radius=12)
        font = pygame.font.SysFont(None, 36)
        tab_label = '<' if not menu_collapsed else '>'
        tab_surf = font.render(tab_label, True, (255,255,255))
        screen.blit(tab_surf, (tab_rect.x + 8, tab_rect.y + 20))
        # Draw UI if menu is open
        if not menu_collapsed:
            # If paused, use a greyed-out color for all controls
            ui_color = (120, 120, 120) if paused else btn_color
            ui_hover = (180, 180, 180) if paused else btn_hover
            slider_col = (120, 120, 120) if paused else slider_color
            handle_col = (180, 180, 180) if paused else handle_color
            # Buttons
            draw_button(screen, add_btn_rect, 'Add 1k', ui_hover if add_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, remove_btn_rect, 'Remove 1k', ui_hover if remove_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, flip_btn_rect, 'Flip Dimension', ui_hover if flip_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, randomise_btn_rect, 'Randomise Positions', ui_hover if randomise_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_slider(screen, speed_slider_rect, SPEED_MIN, SPEED_MAX, speed, slider_col, handle_col, label="Speed")
            draw_slider(screen, steering_slider_rect, STEERING_MIN, STEERING_MAX, steering_strength, slider_col, handle_col, label="Steering")
            draw_slider(screen, res_slider_rect, res_min, res_max, res_grid_size, slider_col, handle_col, label="BG Res")
            draw_toggle(screen, toggle_rect, show_density_bg, "BG On")
            draw_slider(screen, color_start_slider_rect, 0, 360, color_start_hue, slider_col, handle_col, label="Color Start")
            draw_slider(screen, color_end_slider_rect, 0, 360, color_end_hue, slider_col, handle_col, label="Color End")
            draw_slider(screen, particle_size_slider_rect, PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX, particle_size, slider_col, handle_col, label="Particle Size")
            draw_slider(screen, particle_shape_slider_rect, 0, 1, particle_shape, slider_col, handle_col, label="Shape (0=Circle, 1=Square)")
            draw_toggle(screen, color_dir_toggle_rect, color_directional, "Dir Color")
            draw_toggle(screen, lfo_toggle_rect, lfo_enabled, "LFO On")
            draw_slider(screen, lfo_amp_slider_rect, LFO_AMP_MIN, LFO_AMP_MAX, lfo_amplitude, slider_col, handle_col, label="LFO Amp")
            draw_slider(screen, lfo_rate_slider_rect, LFO_RATE_MIN, LFO_RATE_MAX, lfo_rate, slider_col, handle_col, label="LFO Rate")
            draw_slider(screen, waveform_slider_rect, 0, 3, waveform, slider_col, handle_col, label=f"Waveform: {waveform_names[int(waveform)]}")
            if not color_directional:
                for i, rect in enumerate(rgb_slider_rects):
                    draw_slider(screen, rect, RGB_MIN, RGB_MAX, rgb_values[i], slider_col, handle_col, label=rgb_slider_labels[i])
            # Display total number of particles at the bottom of the menu
            font = pygame.font.SysFont(None, 36)
            count_surf = font.render(f"Particles: {len(particles)}", True, (200,200,200) if paused else (255,255,255))
            screen.blit(count_surf, (menu_x + 20, HEIGHT - 60))
            # Draw reset and exit buttons
            draw_button(screen, reset_btn_rect, 'Reset', ui_hover if reset_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, exit_btn_rect, 'Exit', ui_hover if exit_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, randomise_sliders_btn_rect, 'Randomise Sliders', ui_hover if randomise_sliders_btn_rect.collidepoint(mouse_pos) else ui_color)
            draw_button(screen, pause_btn_rect, 'Pause' if not paused else 'Resume', ui_hover if pause_btn_rect.collidepoint(mouse_pos) else ui_color)

        if not paused:
            for idx, p in enumerate(particles):
                p.update(t, flip_dim, speed, steering_strength, lfo_enabled, lfo_amplitude, lfo_rate, waveform)
                p.draw(screen, color_start_hue, color_end_hue, particle_size, particle_shape, color_directional, rgb_values, idx, len(particles))
        else:
            for idx, p in enumerate(particles):
                p.draw(screen, color_start_hue, color_end_hue, particle_size, particle_shape, color_directional, rgb_values, idx, len(particles))

        pygame.display.flip()
        t += 0.005
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()