import tkinter as tk
import random as r

dt = 0.1
dim = 3
G = 1
friction = 0

camspeed = 10


class Keys:
    def __init__(self):
        self.keys = {}

    def is_pressed(self, key):
        return self.keys.get(key, False)
keys = Keys()


class WorldCenter:
    x = 0
    y = 0


class Camera:
    def __init__(self, screen_width, screen_height, tracebles = set([WorldCenter()])):
        self.x = 0
        self.y = 0
        self.scale = 0.2

        self.screen_height = screen_height
        self.screen_width = screen_width

        self.tracebles = tracebles

    def move(self, x, y):
        self.x += x / self.scale
        self.y += y / self.scale

    def scaling(self, scale):
        self.scale *= scale

    def coord(self, x, y):
        traceX = 0
        traceY = 0
        tracelen = len(self.tracebles)
        for planet in self.tracebles:
            traceX += planet.x
            traceY += planet.y
        X = (-self.x + x - traceX/tracelen)*self.scale + self.screen_width/2
        Y = (-self.y + y - traceY/tracelen)*self.scale + self.screen_height/2
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
            # self.pathway = [[x, y], [x, y]]

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.accelerateX = 0
        self.accelerateY = 0

    def acceleratingX(self, F):
        self.accelerateX = F * self.mass

    def acceleratingY(self, F):
        self.accelerateY = F * self.mass

    def update_speed(self, Fx, Fy):
        self.vx += (Fx + self.accelerateX) / self.mass * dt
        self.vy += (Fy + self.accelerateY) / self.mass * dt

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

    def add_planet(self, planet):
        self.planets.append(planet)

    def update(self):
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

    def clear(self, canvas):
        canvas.delete('all')

    def __str__(self):
        return '\n'.join(list(map(str, self.planets)))


camera = Camera(1920, 1080)
scene = Scene(camera)

# scene.add_planet(Planet(105 , 100, 0, 0))
# scene.add_planet(Planet(100, 700, 0, 0))
# scene.add_planet(Planet(50, 800, 0, 0))

# Ship = Ship(10000, 10000, 0, 0, density = 100000, radius = 100, show_pathway = True, color = "#"+("%06x"%r.randint(0,16777215)))
# scene.add_planet(Ship)
# camera.set_tracebles(Ship)

# for i in range(10):
#     planet = Planet(r.uniform(-1000, 1000), r.uniform(-1000, 1000), r.uniform(-10, 10), r.uniform(10, -10), density = 10 ** r.uniform(-1, 1), radius = r.uniform(5, 20), 
#         show_pathway = True, color = "#"+("%06x"%r.randint(0,16777215)))
#     scene.add_planet(planet)
    # camera.add_traceble(planet)

Sun = Planet(0, 0, 0, 0, radius = 100, density = 100, show_pathway = False, color = 'yellow')
Moon = Planet(-1500, 0, 0, 300, density = 1, show_pathway = True, color = 'grey')
Earth = Planet(-1460, 0, 0, 316, radius = 20, density = 1, show_pathway = True, color = 'blue')

scene.add_planet(Sun)
scene.add_planet(Moon)
scene.add_planet(Earth)

# GtivanSun = Planet(1000000, 1000000, 0, 0, radius = 300000)
# scene.add_planet(GtivanSun)

camera.set_tracebles(Earth)


master = tk.Tk()
canvas = tk.Canvas(master, width = 1920, height = 1080, background = 'black')
canvas.pack()


def main():
    if keys.is_pressed('w'):
        camera.move(0, -camspeed)
    if keys.is_pressed('s'):
        camera.move(0, camspeed)
    if keys.is_pressed('d'):
        camera.move(camspeed, 0)
    if keys.is_pressed('a'):
        camera.move(-camspeed, 0)        
    if keys.is_pressed('equal'):
        camera.scaling(1.1)
    if keys.is_pressed('minus'):
        camera.scaling(0.9)
    if keys.is_pressed('space'):
        scene.draw(canvas)
        master.after(0, main)
        return

    # accel = 1000000
    # if keys.is_pressed('Up'):
    #     Ship.acceleratingY(-accel)
    # elif keys.is_pressed('Down'):
    #     Ship.acceleratingY(accel)
    # else:
    #     Ship.acceleratingY(0)
    # if keys.is_pressed('Right'):
    #     Ship.acceleratingX(accel)
    # elif keys.is_pressed('Left'):
    #     Ship.acceleratingX(-accel)
    # else:
    #     Ship.acceleratingX(0)

    scene.update()
    scene.draw(canvas)
    master.after(5, main)

def key_press(e):
    keys.keys[e.keysym] = True

def key_release(e):
    keys.keys[e.keysym] = False

master.state('zoomed')

master.after(0, main)
master.bind('<KeyPress>', key_press)
master.bind('<KeyRelease>', key_release)
master.mainloop()