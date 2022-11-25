import pygame, random, math, time

from pygame.locals import(
    K_ESCAPE,
    KEYDOWN,
    QUIT
)

pygame.init()

# Configuration

# Display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

DEFAULT_BLOB_SIZE = (20, 10)

DISPLAY_VISION_CONES = False

# Blob characteristics
HUNTER_SPEED = 5
RUNNER_SPEED = 3

VISION_RANGE = 500

# Start configuration
STARTCOUNT_HUNTER = 2
STARTCOUNT_RUNNER = 10

# Timings
TICK_TIME = 100/60 # Number of ms between sprite moves

RUNNER_SPLIT_AGE = 200
HUNTER_NOKILL_DIE_AGE = 200

SPAWN_TIME_RUNNER = 10000
SPAWN_TIME_HUNTER = 10000

MAX_RUNNERS = 50
MAX_HUNTERS = 50
MAX_NPCS = 100


# Loading images
img_blob_green_raw = pygame.image.load("img/blob-green.png")
img_blob_red_raw = pygame.image.load("img/blob-red.png")
img_blob_grey_raw = pygame.image.load("img/blob-grey.png")

img_blob_green_scaled = pygame.transform.scale(img_blob_green_raw, DEFAULT_BLOB_SIZE)
img_blob_red_scaled = pygame.transform.scale(img_blob_red_raw, DEFAULT_BLOB_SIZE)
img_blob_grey_scaled = pygame.transform.scale(img_blob_grey_raw, DEFAULT_BLOB_SIZE)

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

ADDNPC = pygame.USEREVENT + 1
ADDHUNTER = pygame.USEREVENT + 2
ADDRUNNER = pygame.USEREVENT + 3

# pygame.time.set_timer(ADDNPC, 1000)
pygame.time.set_timer(ADDHUNTER, SPAWN_TIME_HUNTER)
pygame.time.set_timer(ADDRUNNER, SPAWN_TIME_RUNNER)

running = True


max_id = 0

class Blob(pygame.sprite.Sprite):
    def __init__(self, type, starting_pos=None):
        super(Blob, self).__init__()
        self.type = type
        # self.player = (type == "player")
        self.hunter = (type == "hunter")
        self.runner = (type == "runner")
        self.speed = 5
        self.id = id(self)
        self.killcount = 0
        self.age = 0
        self.nokillage = 0
        self.vision_range = VISION_RANGE
        self.angle = 180

        # if self.player:
        #     self.surf = pygame.Surface((75, 25))
        #     self.surf.fill((52, 171, 235))
        #     self.rect = self.surf.get_rect()

        if self.hunter:
            self.orig_image = self.image = img_blob_red_scaled
            self.speed = HUNTER_SPEED
            # self.surf = pygame.Surface((20, 10))
            # self.surf.fill((227, 50, 197))

        elif self.runner:
            self.orig_image = self.image = img_blob_green_scaled
            self.speed = RUNNER_SPEED
            # self.surf = pygame.Surface((20, 10))
            # self.surf.fill((80, 196, 33))

        else:
            self.orig_image = self.image = img_blob_grey_scaled
            # self.surf = pygame.Surface((20, 10))
            # self.surf.fill((154, 161, 151))

        self.rect = self.orig_image.get_rect()

        if starting_pos:
            self.rect = self.rect.move((starting_pos[0], starting_pos[1]))
            # self.rect = self.surf.get_rect(
            #     center=(starting_pos[0], starting_pos[1])
            # )
        else:
            self.rect = self.rect.move(
                (random.randint(0, SCREEN_WIDTH),
                 random.randint(0, SCREEN_HEIGHT))
            )
            # self.rect = self.surf.get_rect(
            #     center=(random.randint(-2, SCREEN_WIDTH),
            #             random.randint(-2, SCREEN_HEIGHT))
            # )


    # Function to check what is in front
    def see(self, angle_min, angle_max, distance):
        start_coords=[self.rect.centerx, self.rect.centery]
        # print("Checking angles " + str(self.angle + angle_min) + ", " + str(self.angle + angle_max))

        angle_rad = math.radians(-self.angle)  # Remember to convert to radians!

        # Finding 0 angle point (straight ahead)
        straight_point = (
            start_coords[0] + math.cos(angle_rad) * distance,
            start_coords[1] + math.sin(angle_rad) * distance
        )

        points = [(self.rect.centerx, self.rect.centery), straight_point]

        for i in [angle_min, angle_max]:

            # Working out angle between start and end points vs x axis
            x_angle = math.radians(-(self.angle + i) % 360)

            # Working out length of adjacent side (x values to move), where hypotenuse is vision range
            x_len = math.cos(x_angle) * distance

            # Working out length of opposite side (y values to move), where hypotenuse is vision range
            y_len = math.sin(x_angle) * distance

            # Combining two to get coordinates of end point
            end_point = (start_coords[0] + x_len, start_coords[1] + y_len)

            # Adding to list of coords
            points.append(end_point)


        # Note min point is the corner of the right, triangle, max point is corner of the left
        # Vision cone - left
        left_cone_points = [points[i] for i in [0,1,3]]

        # Vision cone - right
        right_cone_points = [points[i] for i in [0,1,2]]

        if DISPLAY_VISION_CONES:

            # Straight forwards line for reference
            pygame.draw.line(
                screen,
                [0, 0, 0],
                (start_coords[0], start_coords[1]),
                (start_coords[0] + math.cos(angle_rad) * distance,
                 start_coords[1] + math.sin(angle_rad) * distance)
            )

            pygame.draw.polygon(
                screen,
                [210, 210, 210],
                right_cone_points, width=0)

            pygame.draw.polygon(
                screen,
                [184, 184, 184],
                left_cone_points, width=0)

        if self.type == "hunter":
            targets = runners
        elif self.type == "runner":
            targets = hunters

        def point_in_triangle(point, triangle_coords):

            # Checking if runner is in the triangle of vision
            # http://www.jeffreythompson.org/collision-detection/tri-point.php

            px = point[0]
            py = point[1]

            x1 = triangle_coords[0][0]
            y1 = triangle_coords[0][1]
            x2 = triangle_coords[1][0]
            y2 = triangle_coords[1][1]
            x3 = triangle_coords[2][0]
            y3 = triangle_coords[2][1]

            areaOrig = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))

            area1 = abs((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py))
            area2 = abs((x2 - px) * (y3 - py) - (x3 - px) * (y2 - py))
            area3 = abs((x3 - px) * (y1 - py) - (x1 - px) * (y3 - py))

            if round(area1 + area2 + area3, 0) == round(areaOrig, 0): # Rounding to account for floating point diffs
                # print("Sighted by " + self.type)
                return True
            else:
                return False

        hits_left = 0
        hits_right = 0

        if self.hunter:
            for i in targets:
                if point_in_triangle((i.rect.centerx, i.rect.centery), left_cone_points):
                    hits_left += 1
                elif point_in_triangle((i.rect.centerx, i.rect.centery), right_cone_points):
                    hits_right += 1

        return {"hits_left": hits_left, "hits_right": hits_right}


    # def hunt(self):

    def move(self, x, y):

        self.rect = self.rect.move(x, y)

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

    def rotate_center(self, angle):
        self.angle = (self.angle - angle) % 360 # Negative rotates clockwise, but we want 'left' as negative so invert here
        # print("Angle change: " + str(angle) + "    New angle: " + str(self.angle))
        self.image = pygame.transform.rotozoom(self.orig_image, self.angle, 1)
        self.rect = self.orig_image.get_rect(center=self.rect.center)

    # Function to decide which way to turn, and how much
    def decide_movement(self, targets):

        # Left: -15
        # Straight: 0
        # Right = 15

        speed_change = 1

        # print(targets)

        if self.runner:
            direction = random.randint(-15, 15) * speed_change

        elif self.hunter:
            if targets["hits_left"] + targets["hits_right"] == 0:
                direction = random.randint(0,3) * speed_change * 10
            elif (targets["hits_left"] > targets["hits_right"]):
                direction = -speed_change
            else:
                direction = speed_change

        return direction

    # Converts a direction to new x and y adjustments
    def convert_direction(self):

        angle_rad = math.radians(-self.angle)  # Remember to convert to radians!
        change = [math.cos(angle_rad), math.sin(angle_rad)]

        return change


    def update(self):

        # x = (random.randint(0, 1) * 2 - 1) * self.speed
        # y = (random.randint(0, 1) * 2 - 1) * self.speed

        # Check vision cone
        targets = self.see(-15, 15, VISION_RANGE)

        # Rotate to new direction
        self.rotate_center(self.decide_movement(targets))

        # Move forwards by speed - converting angle to x and y coord change
        coords = self.convert_direction()

        x = coords[0] * self.speed
        y = coords[1] * self.speed

        self.move(x, y)

    def replicate(self):
        new_blob = Blob(type=self.type, starting_pos=[self.rect.centerx, self.rect.centery])

        if self.hunter:
            if len(hunters) < MAX_HUNTERS:
                all_sprites.add(new_blob)
                hunters.add(new_blob)
        elif self.runner:
            if len(runners) < MAX_RUNNERS:
                all_sprites.add(new_blob)
                runners.add(new_blob)
        elif self.npc:
            if len(npcs) < MAX_NPCS:
                all_sprites.add(new_blob)
                npcs.add(new_blob)

        print("Blob {} replicated, creating blob {}".format(self.id, new_blob.id))


# player = Blob(type = "player")

npcs = pygame.sprite.Group()
hunters = pygame.sprite.Group()
runners = pygame.sprite.Group()

all_sprites = pygame.sprite.Group()
# all_sprites.add(player)

clock = pygame.time.Clock()

time_elapsed = 0

for i in range(0, STARTCOUNT_HUNTER):
    new_hunter = Blob(type="hunter")
    hunters.add(new_hunter)
    all_sprites.add(new_hunter)

for i in range(0, STARTCOUNT_RUNNER):
    new_runner= Blob(type="runner")
    runners.add(new_runner)
    all_sprites.add(new_runner)

while running:

    # clock.tick(60)

    dt = clock.tick(60)
    time_elapsed += dt

    # Did the user click the window close button?
    for event in pygame.event.get():

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

        elif event.type == pygame.QUIT:
            running = False

        elif event.type == ADDNPC and len(npcs) < MAX_NPCS:
            new_npc = Blob(type="npc")
            npcs.add(new_npc)
            all_sprites.add(new_npc)

        elif event.type == ADDHUNTER and len(hunters) < MAX_HUNTERS:
            new_hunter = Blob(type="hunter")
            hunters.add(new_hunter)
            all_sprites.add(new_hunter)

        elif event.type == ADDRUNNER and len(runners) < MAX_RUNNERS:
            new_runner = Blob(type="runner")
            runners.add(new_runner)
            all_sprites.add(new_runner)
        else:
            continue

    # print(time_elapsed)
    if time_elapsed > TICK_TIME:

        screen.fill((255, 255, 255))

        time_elapsed = 0

        collision_dict = pygame.sprite.groupcollide(hunters, runners, False, True)

        for h, rs in collision_dict.items():
            h.killcount += len(rs)

            print("Hunter {} ate runner(s) ".format(str(h.id)) + ", ".join([str(r.id) for r in rs]) + ". Total kills: {}".format(str(h.killcount)))
            h.replicate()
            h.nokillage = 0

        for r in runners:
            if r.age >= RUNNER_SPLIT_AGE:
                print("Runner {} survived for {} ticks and replicated".format(str(r.id), str(RUNNER_SPLIT_AGE)))
                r.replicate()

        for h in hunters:
            if h.nokillage >= HUNTER_NOKILL_DIE_AGE:
                print("Hunter {} didn't get a kill for {} ticks and died".format(str(h.nokillage), str(HUNTER_NOKILL_DIE_AGE)))
                h.kill()

        for b in all_sprites:
            b.age += 1
            b.nokillage += 1


        npcs.update()
        hunters.update()
        runners.update()

        for entity in all_sprites:
            screen.blit(entity.image, entity.rect)

        pygame.display.flip()

pygame.quit()

for h in hunters:
    print("Hunter {} kills: {}".format(str(h.id), str(h.killcount)))
