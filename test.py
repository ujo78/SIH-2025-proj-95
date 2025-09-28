from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, NodePath

class CarModelDemo(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()

        self.car = self.loader.loadModel("Car.egg")
        self.car.setScale(0.5)
        self.car.setPos(0, 0, 1.6)  # Lift car slightly
        self.car.reparentTo(self.render)

        self.camera.setPos(10, -30, 10)
        self.camera.lookAt(self.car)

     
        ground_cm = CardMaker("ground")
        ground_cm.setFrame(-100, 100, -100, 100)
        ground = NodePath(ground_cm.generate())
        ground.setP(-90)
        ground.setPos(0, 0, 0)
        ground.setColor(0.2, 0.8, 0.2, 1)
        ground.reparentTo(self.render)

        self.building_model = self.loader.loadModel("building.egg")
        self.scale_x =0.1
        self.scale_y=0.1
        self.scale_z=5
        self.building_model.setScale(self.scale_x, self.scale_y, self.scale_z)
      

        self.disableMouse()  

        self.camera_distance = 50
        self.camera_pitch = 20  
        self.camera_heading = 0  

        self.last_mouse_pos = None
        self.is_dragging = False

        self.update_camera()

        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)

        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        self.taskMgr.add(self.camera_task, "camera-task")

    def update_camera(self):
        from math import radians, sin, cos

        pitch_rad = radians(self.camera_pitch)
        heading_rad = radians(self.camera_heading)


        x = self.camera_distance * cos(pitch_rad) * sin(heading_rad)
        y = -self.camera_distance * cos(pitch_rad) * cos(heading_rad)
        z = self.camera_distance * sin(pitch_rad)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(0, 0, 0)  # Look at origin; adjust as needed

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.is_dragging = True
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            self.last_mouse_pos = (x, y)

    def stop_drag(self):
        self.is_dragging = False
        self.last_mouse_pos = None

    def camera_task(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            x, y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]
            self.last_mouse_pos = (x, y)

            self.camera_heading += dx * 100
            self.camera_pitch += dy * 100

            self.camera_pitch = max(-89, min(89, self.camera_pitch))

            self.update_camera()
        return task.cont

    def zoom_in(self):
        self.camera_distance = max(10, self.camera_distance - 5)
        self.update_camera()

    def zoom_out(self):
        self.camera_distance = min(100, self.camera_distance + 5)
        self.update_camera()

        def add_building_instance(x, y, height=15):
            building_instance = self.building_model.copyTo(self.render)
            building_instance.setPos(x, y, height / 2 - 10)
          
            building_instance.setScale(self.scale_x,self.scale_y,self.scale_z/15)  # Assuming original height is 15 units
            building_instance.setColor(0.85, 0.85, 0.88, 1)  # Optional color tint
            return building_instance

        spacing = 40
        for xi in range(-80, 81, spacing):
            for yi in range(-80, 81, spacing):
                if abs(xi) > 20 or abs(yi) > 20:
                    height = 10 + (abs(xi + yi) % 3) * 7
                    add_building_instance(xi, yi, height=height)

app = CarModelDemo()
app.run()
