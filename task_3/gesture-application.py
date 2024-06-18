import pyglet
from pyglet.window import mouse
import xml.etree.ElementTree as ET
import time
import os
import random
import numpy as np
from sklearn.preprocessing import LabelEncoder,StandardScaler
from scipy.signal import resample

# XML parser
import xml.etree.ElementTree as ET
import keras


NUM_POINTS = 50
RECOGNIZER = keras.models.load_model("gesture_recognition.keras")

LABELS = ['x', 'circle', 'triangle']

encoder = LabelEncoder()
labels_encoded = encoder.fit_transform(LABELS)
drawed_gestures = []

# Gesture recognition part of the code
def preproces_data(points):

    points = np.array(points, dtype=float)
                    
    scaler = StandardScaler()
    points = scaler.fit_transform(points)
                    
    resampled = resample(points, NUM_POINTS)
    # show points on the screen
    for i in range(len(resampled)):
        x = resampled[i][0]
        y = resampled[i][1]
        drawed_gestures.append(pyglet.shapes.Circle(x, y, 5, color=(255, 0, 0)))

    return resampled

# The prediction is not working properly, i'm having a similar problem to taks 2, but due to the smaller
# amount of gestures to predit, the model is able to predict it correctly sometimes, but most of the time
# it predicts the wrong gesture

def predict_gesture(points):
    points = preproces_data(points)
    print(points)
    result = RECOGNIZER.predict(np.array([points]))
    prediction = np.argmax(result)
    prediction_label = encoder.inverse_transform(np.array([prediction]))[0]
    return prediction_label

# Game part of the code
GAME_WIDTH = 800
GAME_HEIGHT = 800
window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
drawing = False
game_started = False
points = []
BACKGROUND = pyglet.sprite.Sprite(pyglet.image.load("./imgs/background.jpg"), x=0, y=0)
FADE_BLOCK = pyglet.shapes.Rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, color=(0, 0, 0, 0))
enemy_img = pyglet.image.load("./imgs/enemy.png")
enemy_img.anchor_x = enemy_img.width // 2
enemy_img.anchor_y = enemy_img.height // 2
ENEMY = pyglet.sprite.Sprite(enemy_img, x=GAME_WIDTH/2, y=GAME_HEIGHT/2)
ENEMY.scale = 4
UPGRADE = pyglet.sprite.Sprite(pyglet.image.load("./imgs/sword.png"), x=100, y=100)
HEAL_IMG = pyglet.image.load("./imgs/heal.png")
HEAL = pyglet.sprite.Sprite(HEAL_IMG, x=100, y=100)

STARTING_HEALTH = 100

class Game:
    def __init__(self):
        self.room = Room().starting_room()
        self.player = Player()
        self.difficulty = 1
        self.enemy_present = False
        self.heal_present = False
        self.upgrade_present = False
        self.score = 0

    def move(self):
        if self.room.enemy:
            print("You can't leave with an enemy in the room")
            return
        
        self.room = self.room.create_room(difficulty=self.difficulty)
        if self.room.item:
            if self.room.item.heal:
                self.heal_present = True
                self.upgrade_present = False
                print("You found a health potion")
                self.player.heals.append(self.room.item.heal)
            else:
                self.upgrade_present = True
                self.heal_present = False
                print("You found a damage upgrade")
                self.player.improve(self.room.item.upgrade)
        else:
            self.heal_present = False
            self.upgrade_present = False
        if self.room.enemy:
            self.enemy_present = True

        if self.difficulty < 10:
            self.difficulty += 1
        pyglet.clock.schedule_once(self.fade_out, 0.1, FADE_BLOCK)
        pyglet.clock.schedule_once(self.fade_in, 0.1, FADE_BLOCK)
        self.score += 1

    def fade_in(self, dt, block):
        # Increase the opacity of the sprite to create a fade in effect
        block.opacity += 10

        # If the sprite is not fully opaque, schedule the next fade in step
        if block.opacity < 255:
            pyglet.clock.schedule_once(self.fade_in, 0.01, block)

    def fade_out(self, dt, block):
        # Decrease the opacity of the sprite to create a fade out effect
        block.opacity -= 10

        # If the sprite is not fully transparent, schedule the next fade out step
        if block.opacity > 0:
            pyglet.clock.schedule_once(self.fade_out, 0.01, block)


    def attack(self):
        if self.room.enemy:
            self.player.attack(self.room.enemy)
            if self.room.enemy.health <= 0:
                self.room.enemy = None
                print("enemy defeated")
                self.enemy_present = False
            

    def heal(self):
        if self.player.heals == []:
            print("You have no health potions")
            return
        self.player.heal(self.player.heals.pop())
    
    def action(self, gesture):
        if gesture == "x":
            self.attack()
        elif gesture == "circle":
            self.heal()
        elif gesture == "triangle":
            self.move()

    def try_enemy_attack(self, dt):
        if self.room.enemy:
            self.room.enemy.attack(self.player)
            if self.player.health <= 0:
                print("You died")
                self = stop_game(self)
        

class Item:
    def __init__(self, heal=0, upgrade=0):
        self.heal = heal
        self.upgrade = upgrade

class Player:
    def __init__(self, heals=[]):
        self.health = STARTING_HEALTH
        self.dmg = 10
        self.heals = heals

    def attack(self, enemy):
        print("Player attacks")
        if enemy:
            # If the player attacks the enemy the enemy attack timer will reset
            enemy.last_attack = time.time()
            enemy.health -= self.dmg

    def add_heal(self, heal):
        print("You found a health potion")
        self.heals.append(heal)

    def heal(self, potion):
        print("You healed")
        if self.health + potion > STARTING_HEALTH:
            self.health = STARTING_HEALTH
        else:
            self.health += potion

    def improve(self, upgrade):
        print("You improved your weapon")
        self.dmg += upgrade

class Enemy:
    def __init__(self, attack_time=10, health=100, dmg=10):
        self.starting_health = health 
        self.health = health
        self.dmg = dmg
        self.attack_time = attack_time
        self.last_attack = time.time()

    def attack(self, player):
        if time.time() - self.last_attack >= self.attack_time:
            print("Enemy attacks")

            # dmg "animation"
            pyglet.shapes.Rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, color=(255, 0, 0)).draw()
            player.health -= self.dmg
            self.last_attack = time.time()

class Room:
    def __init__(self, enemy=Enemy(), item=None):
        self.enemy = enemy
        self.item = item

    def starting_room(self):
        room = Room(enemy=None,item=Item(heal=100))
        return room

    def create_room(self, difficulty=1):
        print("You entered a new room")
        # Chance of an enemy spawning is the difficulty divided by 5
        enemy_spawing = random.randint(1, 5) <= difficulty
        item_spawing = random.randint(1, 10) >= difficulty
        item_type = random.randint(1, 2)
        
        item = None
        enemy = None

        if item_spawing:
            if item_type == 1:
                item = Item(heal=100)
            else:
                item = Item(upgrade=5)
        # The higher the diffulty the more often an enemy will attack, if the player attacks before the enemy
        # the enemy attack timer will reset
        if enemy_spawing:
            print("An enemy appeared")
            enemy = Enemy(health=20*difficulty, attack_time=10/difficulty)
        
        return Room(enemy, item)
        

game = Game()

def stop_game(game):
    global game_started
    game_started = False
    return Game()

@window.event
def on_draw():
    global game_started
    window.clear()
    if not game_started:
        pyglet.text.Label("Press space to start", x=GAME_WIDTH/2, y=600, anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label("Use mouse to draw gestures", x=GAME_WIDTH/2, y=GAME_HEIGHT/2, anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label("x = attack", x=GAME_WIDTH/2, y=300, anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label("circle = heal", x=GAME_WIDTH/2, y=250, anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label("triangle = move", x=GAME_WIDTH/2, y=200, anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label("You can only move on after the enemy has been defeated", x=GAME_WIDTH/2, y=150, anchor_x='center', anchor_y='center').draw()
    else:
        BACKGROUND.draw()
        FADE_BLOCK.draw()
        pyglet.text.Label("Health: " + str(game.player.health), x=50, y=80).draw()
        pyglet.shapes.Rectangle(50, 50, STARTING_HEALTH*3, 20, color=(100, 100, 100)).draw()
        pyglet.shapes.Rectangle(50, 50, game.player.health*3, 20, color=(0, 255, 0)).draw()
        pyglet.text.Label("Score: " + str(game.score), x=GAME_WIDTH/2, y=20).draw()
        if game.player.heals:
            for i in range(len(game.player.heals)):
                pyglet.sprite.Sprite(HEAL_IMG,GAME_WIDTH-100, GAME_HEIGHT-(80*i)-100).draw()
        if game.enemy_present:
            ENEMY.draw()
            pyglet.text.Label("Enemy Health: " + str(game.room.enemy.health), x=50, y=750).draw()
            pyglet.shapes.Rectangle(50, 700, game.room.enemy.starting_health*3, 20, color=(100, 100, 100)).draw()
            pyglet.shapes.Rectangle(50, 700, game.room.enemy.health*3, 20, color=(0, 255, 0)).draw()
        if game.heal_present:
            HEAL.draw()
            pyglet.text.Label("Health potion added to inventory", x=GAME_WIDTH/2, y=100, anchor_x='center', anchor_y='center').draw()
            #show_animation(HEAL, 0.01)
        if game.upgrade_present:
            pyglet.text.Label("Weapon upgrade! +10 dmg", x=GAME_WIDTH/2, y=100, anchor_x='center', anchor_y='center').draw()
            UPGRADE.draw()
            #show_animation(HEAL, 0.01)
        if drawing:
            if len(points) > 1:
                for i in range(len(points)):
                    if i == 0:
                        pass
                    else:
                        pyglet.shapes.Line(points[i-1][0], points[i-1][1], points[i][0], points[i][1], width=5).draw()

@window.event
def on_mouse_press(x, y, button, modifiers):
    global drawing
    if button == mouse.LEFT:
        drawing = True
        points.append((x, y))

@window.event
def on_mouse_release(x, y, button, modifiers):
    global drawing
    if button == mouse.LEFT:
        drawing = False
        gesture = predict_gesture(points)
        points.clear()
        game.action(gesture)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if drawing:
        points.append((x, y))


# Keyboard input still implemented due to the gesture recognition not working properly

@window.event
def on_key_press(symbol, modifiers):
    global game_started
    if not game_started:
        if symbol == pyglet.window.key.SPACE:
            game_started = True
    else:
        if symbol == pyglet.window.key.SPACE:
            game.action("x")
        if symbol == pyglet.window.key.UP:
            game.action("triangle")
        if symbol == pyglet.window.key.ENTER:
            game.action("circle")

pyglet.clock.schedule_interval(game.try_enemy_attack, 1)
pyglet.app.run()

# Things to do:
# add heals view
