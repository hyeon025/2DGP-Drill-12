from pico2d import *

import random
import math

import common
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0


        self.tx, self.ty = 1000, 1000

        self.patrol_points =  [(43, 274), (1118, 274), (1050, 494), (575, 804), (235, 991), (575, 804), (1050, 494), (1118, 274)]
        self.loc_no = 0

        self.build_behavior_tree()




    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION

        self.bt.run()



    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        Zombie.marker_image.draw(self.tx+25, self.ty-25)



        draw_rectangle(*self.get_bb())
        draw_circle(self.x, self.y, int(PIXEL_PER_METER * 7), 255,255,0)

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        # 여기를 채우시오.
        if x is None or y is None:
            raise ValueError('목적지 좌표가 주어지지 않았습니다.')
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS
        pass



    def distance_less_than(self, x1, y1, x2, y2, r):

        distance2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2
        pass



    def move_little_to(self, tx, ty):
        self.dir = math.atan2(ty-self.y, tx-self.x)
        distance = game_framework.frame_time * RUN_SPEED_PPS
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)
        pass



    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_little_to(self.tx, self.ty)

        if self.distance_less_than(self.tx, self.ty, self.x,self.y,r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass



    def set_random_location(self):
        self.tx, self.ty = random.randint(100, 1180), random.randint(100, 924)
        return BehaviorTree.SUCCESS
        pass


    def if_boy_nearby(self, distance):
        if self.distance_less_than(self.x, self.y, common.boy.x, common.boy.y, distance):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL


    def move_to_boy(self, r=0.5):
        self.state = 'Walk'
        self.move_little_to(common.boy.x, common.boy.y)
        if self.distance_less_than(self.x, self.y, common.boy.x, common.boy.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING #아직 소년에게 가지 않음


    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_points[self.loc_no]
        self.loc_no = (self.loc_no + 1) % len(self.patrol_points)
        return BehaviorTree.SUCCESS
        pass


    def build_behavior_tree(self):
        a1 = Action("목적지 설정",self.set_target_location,800,800)

        a2 = Action("목적지로 이동",self.move_to)

        root = move_to_target_location = Sequence("지정된 목적지로 이동",a1,a2)

        a3 = Action("랜덤위치 설정",self.set_random_location)
        wander = Sequence("랜덤위치로 이동",a3,a2)

        c1 = Condition('소년이 근처에 있는가?', self.if_boy_nearby, 7)
        a4 = Action('소년한테 접근', self.move_to_boy)
        chase_boy_if_nearby = Sequence('소년이 근처에 있으면 추적', c1, a4)

        chase_or_wander = Selector('추적 아니면 배회',chase_boy_if_nearby,wander)

        a5 = Action('다음 순찰 위치 획득', self.get_patrol_location)
        root = patrol = Sequence('순찰', a5, a2)

        root = chase_or_wander = Selector('추적 아니면 배회', chase_boy_if_nearby, patrol)

        self.bt = BehaviorTree(root)



