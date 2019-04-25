import tkinter as tk
import random as r
import time

dt = 0.1
dim = 3
G = 1
friction = 0

accel = 300
camspeed = 10
scalespeed = 0.1


class Controller:
    binds = {}
    keys = {}

    def is_pressed(self, key):
        return self.keys.get(key, False)

    def change_key_state(self, key, state):
        if self.is_pressed(key) != state:
            if state:
                self.binds.get(('op', key), lambda: 0)()
            else:
                self.binds.get(('or', key), lambda: 0)()
            self.keys[key] = state

    def bind(self, control_type, keysym, function):
        """
        control_type - on_press 'op', on_release 'or', while_pressed 'wp', while_released 'wr'
        """
        self.binds[(control_type, keysym)] = function

    def unbind(self, control_type, keysym):
        self.binds.pop((control_type, keysym))

    def update(self):
        for (control_type, keysym) in self.binds:
            if (control_type == 'wp' and self.is_pressed(keysym)) or\
               (control_type == 'wr' and not self.is_pressed(keysym)):
                self.binds[(control_type, keysym)]()

controller = Controller()



class WorldCenter:
    x = 0
    y = 0
    mass = 1


class Camera:
    def __init__(self, screen_width, screen_height, tracebles = set([WorldCenter()])):
        self.x = 0
        self.y = 0
        self.scale = 1

        self.screen_height = screen_height
        self.screen_width = screen_width

        self.tracebles = tracebles

    def move(self, x, y):
        self.x += x * self.scale
        self.y += y * self.scale

    def scaling(self, scale):
        self.scale *= 2**scale

    def coord(self, x, y):
        traceX = 0
        traceY = 0
        tracelen = len(self.tracebles)
        for planet in self.tracebles:
            traceX += planet.x
            traceY += planet.y
        X = (-self.x + x - traceX/tracelen)/self.scale + self.screen_width/2
        Y = (-self.y + y - traceY/tracelen)/self.scale + self.screen_height/2
        return X, Y

    def set_tracebles(self, traceble):
        self.tracebles = set([traceble])

    def add_traceble(self, traceble):
        self.tracebles.add(traceble)


class Planet:
    def __init__(self, x, y, vx, vy, radius = 10, density = 1, show_pathway = False, path_length = 200, color = 'red'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

        self.radius = radius
        self.mass = self.radius ** dim * density
        self.friction = friction

        self.show_pathway = show_pathway
        if self.show_pathway:
            self.path_length = path_length
            self.pathcolor = color
            self.pathway = [[x, y][:] for _ in range(self.path_length)]

        self.color = color

    def update_coords(self):
        self.x += dt * self.vx
        self.y += dt * self.vy

        if self.show_pathway:
            self.pathway.pop(0)
            self.pathway.append([self.x, self.y])

    def update_speed(self, Fx, Fy):
        self.vx += Fx / self.mass * dt
        self.vy += Fy / self.mass * dt

    def update(self, Fx, Fy):
        self.update_coords()
        self.update_speed(Fx, Fy)

    def draw(self, canvas, camera):
        canvas.create_oval(*camera.coord(self.x - self.radius, self.y - self.radius), *camera.coord(self.x + self.radius, self.y + self.radius), fill=self.color)

        if self.show_pathway:
            for i in range(len(self.pathway) - 1):
                canvas.create_line(camera.coord(self.pathway[i][0], self.pathway[i][1]), camera.coord(self.pathway[i+1][0], self.pathway[i+1][1]), fill=self.pathcolor)

    def __str__(self):
        return'<Planet. x: {}; y: {}>'.format(self.x, self.y)


class Ship(Planet):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.accelerateFX = 0
        self.accelerateFY = 0

        controller.bind('wp', 'Up', lambda: self.acceleratingY(-accel))
        controller.bind('wp', 'Down', lambda: self.acceleratingY(accel))
        controller.bind('wp', 'Right', lambda: self.acceleratingX(accel))
        controller.bind('wp', 'Left', lambda: self.acceleratingX(-accel))

        controller.bind('or', 'Up', lambda: self.acceleratingY(accel))
        controller.bind('or', 'Down', lambda: self.acceleratingY(-accel))
        controller.bind('or', 'Right', lambda: self.acceleratingX(-accel))
        controller.bind('or', 'Left', lambda: self.acceleratingX(accel))

    def acceleratingX(self, accel):
        self.accelerateFX += accel * self.mass

    def acceleratingY(self, accel):
        self.accelerateFY += accel * self.mass

    def update_speed(self, Fx, Fy):
        self.vx += (Fx + self.accelerateFX) / self.mass * dt
        self.vy += (Fy + self.accelerateFY) / self.mass * dt
        self.accelerateFY = 0
        self.accelerateFX = 0

    def __str__(self):
        return'<Ship. x: {}; y: {}>'.format(self.x, self.y)



def dist_2(planet1, planet2):
    return (planet1.x - planet2.x) ** 2 + (planet1.y - planet2.y) ** 2 + friction

def force(planet1, planet2):
    return G * planet1.mass * planet2.mass / (dist_2(planet1, planet2) ** ((dim - 1) / 2))

def force_x(planet1, planet2):
    _force = force(planet1, planet2)
    k = (planet2.x - planet1.x) / dist_2(planet1, planet2) ** 0.5
    return _force * k

def force_y(planet1, planet2):
    _force = force(planet1, planet2)
    k = (planet2.y - planet1.y) / dist_2(planet1, planet2) ** 0.5
    return _force * k


class Scene:
    def __init__(self, camera):
        self.planets = []
        self.camera = camera
        self.is_paused = False

    def add_planet(self, planet):
        self.planets.append(planet)

    def update(self):
        if self.is_paused:
            return
        planetslen = len(self.planets)
        forces = [[0, 0][:] for _ in range(planetslen)] 
        for i in range(planetslen):
            for j in range(planetslen):
                if i != j:
                    forces[i][0] += force_x(self.planets[i], self.planets[j])
                    forces[i][1] += force_y(self.planets[i], self.planets[j])

        for i in range(planetslen):
            self.planets[i].update(*forces[i])

    def draw(self, canvas):
        self.clear(canvas)
        for planet in self.planets:
            planet.draw(canvas, camera)

    def play_pause(self):
        self.is_paused = not self.is_paused

    def play(self):
        self.is_paused = False

    def pause(self):
        self.is_paused = True

    def clear(self, canvas):
        canvas.delete('all')

    def __str__(self):
        return '\n'.join(list(map(str, self.planets)))



camera = Camera(1920, 1080)
scene = Scene(camera)

# ship = Ship(controller, 10000, 10000, 0, 0, density = 10, radius = 100, show_pathway = True, color = "#"+("%06x"%r.randint(0,16777215)))
# scene.add_planet(ship)
# camera.set_tracebles(ship)

# for i in range(3):
#     planet = Planet(r.uniform(-1000, 1000), r.uniform(-1000, 1000), r.uniform(-10, 10), r.uniform(10, -10), density = 10 ** r.uniform(-1, 1), radius = r.uniform(5, 20), 
#         show_pathway = True, color = "#"+("%06x"%r.randint(0,16777215)))
#     scene.add_planet(planet)
#     camera.add_traceble(planet)

Sun = Planet(0, 0, 0, 0, radius = 100, density = 100, show_pathway = True, color = 'yellow')
Moon = Planet(-1500, 0, 0, 300, density = 1, show_pathway = True, color = 'grey')
Earth = Planet(-1460, 0, 0, 316, radius = 20, density = 1, show_pathway = True, color = 'blue')

scene.add_planet(Sun)
scene.add_planet(Moon)
scene.add_planet(Earth)
camera.set_tracebles(Earth)

# GtivanSun = Planet(100000, 100000, 0, 0, radius = 10000)
# scene.add_planet(GtivanSun)



master = tk.Tk()
canvas = tk.Canvas(master, width = 1920, height = 1080, background = 'black')

controller.bind('wp', 'w', lambda: camera.move(0, -camspeed))
controller.bind('wp', 's', lambda: camera.move(0, camspeed))
controller.bind('wp', 'a', lambda: camera.move(-camspeed, 0))
controller.bind('wp', 'd', lambda: camera.move(camspeed, 0))
controller.bind('wp', 'equal', lambda: camera.scaling(-scalespeed))
controller.bind('wp', 'minus', lambda: camera.scaling(scalespeed))

controller.bind('op', 'space', scene.pause)
controller.bind('or', 'space', scene.play)

def main():
    t1 = time.time()

    controller.update()
    scene.update()
    scene.draw(canvas)
    canvas.create_text(20, 1000, anchor = 'sw', text = 'scale: {}'.format(camera.scale), fill = 'white')

    t5 = time.time()

    master.after(50 - int(1000*(t5 - t1)), main)

def key_press(e):
    controller.change_key_state(e.keysym, True)

def key_release(e):
    controller.change_key_state(e.keysym, False)


canvas.pack()
master.state('zoomed')
master.after(0, main)
master.bind('<KeyPress>', key_press)
master.bind('<KeyRelease>', key_release)
master.mainloop()