import pygame
import sys
import random
from pygame import mixer
from datetime import datetime, timedelta
import dataclasses

# Инициализация Pygame
pygame.init()
mixer.init()

# Настройки экрана
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Дорога жизни")

# Цвета
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
GRAY = pygame.Color(100, 100, 100)
BLUE = pygame.Color(50, 50, 150)
RED = pygame.Color(150, 50, 50)
DARK_RED = pygame.Color(100, 0, 0)
GOLD = pygame.Color(218, 165, 32)

# Шрифты (адаптивные размеры)
font_large = pygame.font.SysFont('arial', HEIGHT // 20)
font_medium = pygame.font.SysFont('arial', HEIGHT // 25)
font_small = pygame.font.SysFont('arial', HEIGHT // 30)
font_historical = pygame.font.SysFont('timesnewroman', HEIGHT // 25)

# Состояния игры
MENU = 0
GAME = 1
GAME_OVER = 2
VICTORY = 3
HISTORY_FACT = 4
SHOW_RESULT = 5
DAY_START = 6

# Исторические даты блокады
BLOCKADE_START = datetime(1941, 9, 8)
BLOCKADE_END = datetime(1944, 1, 27)

# Ограничение частоты кадров
MAX_FPS = 30

@dataclasses.dataclass
class Button:
    rect: pygame.Rect  # прямоугольник кнопки
    fill_color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(WHITE))  # цвет заливки
    outline_width: int = 0  # ширина обводки
    outline_color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(WHITE))  # цвет обводки

    # отрисовывает кнопку на экран
    def draw(self):
        pygame.draw.rect(screen, self.fill_color, self.rect)
        pygame.draw.rect(screen, self.outline_color, self.rect, self.outline_width)
    
    # проверяет находится ли точка point в кнопке
    def contains_point(self, point: tuple[int, int]) -> bool:
        return self.rect.collidepoint(point)

@dataclasses.dataclass
class Text:
    origin: tuple[int, int]  # точка - центр текста
    font: pygame.font.Font  # шрифт текста
    text: str = "Это Текст!"  # текст
    width: int = -1  # ширина по которой разделять на строки
    color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(BLACK))  # цвет текста
    should_center: bool = True  # центрировать ли текст

    # отрисовывает текст на экран
    def draw(self):
        current_y = self.origin[1]
        for line in self.wrap_text():
            text_surface = self.font.render(line, True, self.color)
            if self.should_center:
                x = self.origin[0] - text_surface.get_width()//2
            else:
                x = self.origin[0]

            screen.blit(text_surface, (x, current_y))
            current_y += text_surface.get_height()
    
    def wrap_text(self):
        if self.width <= 0:
            return [self.text]

        words = self.text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]
            
            if test_width < self.width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines


class Game:
    def __init__(self):
        self.is_running = True  # Должна ли игра продолжать работать
        self.fps_clock = pygame.time.Clock()  # Часы для ограничения частоты кадров
        self.buttons: list[Button] = []
        self.state = MENU
        self.day = 1
        self.max_days = 5
        self.food = 0
        self.health = 100
        self.morale = 100
        self.ice_stability = 100
        self.story_progress = 0
        self.current_scene = None
        self.choices = []
        self.date = BLOCKADE_START
        self.history_facts_shown = []
        self.waiting_for_choice = False
        self.result_text = ""
        self.load_assets()
        self.load_story()
        self.load_history_facts()

    def load_assets(self):
        # Создаем случайные изображения с тематическими цветами
        self.images = {
            'menu_bg': self.create_image((50, 70, 90)),  # Темно-синий
            'scene1': self.create_image((80, 80, 100)),  # Серый (база)
            'scene2': self.create_image((70, 90, 80)),   # Холодный (лёд)
            'scene3': self.create_image((90, 70, 80)),   # Теплый (город)
            'scene4': self.create_image((60, 80, 90)),   # Синий (метель)
            'scene5': self.create_image((90, 60, 70)),   # Красный (атака)
            'history1': self.create_image((70, 70, 90)),
            'history2': self.create_image((80, 80, 70)),
            'history3': self.create_image((90, 70, 80))
        }
        
        # Заглушки для звуков
        self.sounds = {
            'menu_music': None,
            'game_music': None,
            'engine': None,
            'ice_crack': None,
            'explosion': None,
            'success': None,
            'failure': None
        }
    
    def create_image(self, base_color):
        """Создает изображение с текстурой"""
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(base_color)
        
        # Добавляем текстуру
        for _ in range(2000):
            x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
            brightness = random.randint(-30, 30)
            color = (
                max(0, min(255, base_color[0] + brightness)),
                max(0, min(255, base_color[1] + brightness)),
                max(0, min(255, base_color[2] + brightness))
            )
            pygame.draw.circle(surface, color, (x, y), random.randint(1, 5))
        
        return surface
    
    def load_story(self):
        self.story_scenes = [
            # День 1
            {
                'text': f"День 1. {self.date.strftime('%d.%m.%Y')}\nВы загружаете грузовик на базе. Сколько продовольствия взять?",
                'image': 'scene1',
                'sound': 'engine',
                'choices': [
                    {"text": "Максимальный груз (250 кг, риск провалиться под лёд)", 
                     "effect": {"success": "Вы загрузили максимальный груз. Будьте осторожны!", 
                               "fail": None, 
                               "food": 250, "health": -20, "morale": -10}},
                    {"text": "Средний груз (150 кг, баланс риска и пользы)", 
                     "effect": {"success": "Вы загрузили средний груз. Разумный выбор.", 
                               "fail": None, 
                               "food": 150, "health": -10, "morale": -5}},
                    {"text": "Минимальный груз (50 кг, безопасно, но мало еды)", 
                     "effect": {"success": "Вы взяли минимальный груз. Городу будет тяжело...", 
                               "fail": None, 
                               "food": 50, "health": 0, "morale": 0}}
                ]
            },
            {
                'text': "День 1. Вы движетесь по льду Ладожского озера. Впереди трещина во льду. Что делать?",
                'image': 'scene2',
                'sound': 'ice_crack',
                'choices': [
                    {"text": "Проехать быстро (риск провалиться)", 
                     "effect": {"success": "Вы успешно проехали трещину на скорости!", 
                               "fail": "Грузовик провалился под лёд! Вы потеряли весь груз.", 
                               "risk": 0.4, "food_loss": 1.0, "health_loss": 30}},
                    {"text": "Проехать медленно (безопаснее)", 
                     "effect": {"success": "Вы осторожно пересекли трещину.", 
                               "fail": "Лёд треснул, но вы успели проехать! Часть груза повреждена.", 
                               "risk": 0.2, "food_loss": 0.3, "health_loss": 10}},
                    {"text": "Объехать (потеря времени, -10% боевого духа)", 
                     "effect": {"success": "Вы выбрали безопасный путь, потеряв время.", 
                               "fail": None, 
                               "food": 0, "health": 0, "morale": -10}}
                ]
            },
            # День 2
            {
                'text': f"День 2. {(self.date + timedelta(days=1)).strftime('%d.%m.%Y')}\nВ небе появляются немецкие самолёты!",
                'image': 'scene5',
                'sound': 'explosion',
                'choices': [
                    {"text": "Ускориться и попытаться уехать", 
                     "effect": {"success": "Вам удалось уйти от бомбёжки!", 
                               "fail": "Прямое попадание! Грузовик уничтожен.", 
                               "risk": 0.5, "food_loss": 1.0, "health_loss": 50}},
                    {"text": "Остановиться и замаскироваться", 
                     "effect": {"success": "Самолёты вас не заметили.", 
                               "fail": "Бомбы упали рядом, грузовик повреждён.", 
                               "risk": 0.3, "food_loss": 0.5, "health_loss": 20}},
                    {"text": "Продолжить движение как есть", 
                     "effect": {"success": "Самолёты пролетели мимо.", 
                               "fail": "Бомба попала в грузовик!", 
                               "risk": 0.7, "food_loss": 0.8, "health_loss": 40}}
                ]
            },
            # День 3
            {
                'text': f"День 3. {(self.date + timedelta(days=2)).strftime('%d.%m.%Y')}\nВы встретили колонну грузовиков. Командир предлагает объединиться.",
                'image': 'scene4',
                'choices': [
                    {"text": "Присоединиться к колонне (+10% боевого духа)", 
                     "effect": {"success": "Вы присоединились к колонне. Движение безопаснее.", 
                               "fail": None, 
                               "food": 0, "health": 0, "morale": 10}},
                    {"text": "Продолжить самостоятельно (риск нападения)", 
                     "effect": {"success": "Вы благополучно доехали одни.", 
                               "fail": "На вас напали! Часть груза украдена.", 
                               "risk": 0.3, "food_loss": 0.4, "health_loss": 15}}
                ]
            },
            # День 4
            {
                'text': f"День 4. {(self.date + timedelta(days=3)).strftime('%d.%m.%Y')}\nНачалась сильная метель! Видимость практически нулевая.",
                'image': 'scene4',
                'choices': [
                    {"text": "Остановиться и переждать (потеря времени, -10 кг продовольствия)", 
                     "effect": {"success": "Вы переждали метель, потеряв немного времени.", 
                               "fail": None, 
                               "food": -10, "health": 0, "morale": 0}},
                    {"text": "Продолжить движение (высокий риск аварии)", 
                     "effect": {"success": "Вы благополучно преодолели метель.", 
                               "fail": "Вы съехали с трассы! Грузовик застрял.", 
                               "risk": 0.6, "food_loss": 0.5, "health_loss": 20}}
                ]
            },
            # День 5
            {
                'text': f"День 5. {(self.date + timedelta(days=4)).strftime('%d.%m.%Y')}\nВы прибыли в Ленинград. Голодные жители смотрят на ваш грузовик.",
                'image': 'scene3',
                'sound': None,
                'choices': [
                    {"text": "Раздать всё продовольствие (+30% боевого духа)", 
                     "effect": {"success": "Вы раздали весь груз. Люди благодарны вам!", 
                               "fail": None, 
                               "food": 0, "health": 0, "morale": 30}},
                    {"text": "Раздать половину (остальное на следующий рейс, +15% боевого духа)", 
                     "effect": {"success": "Вы раздали половину груза, сохранив часть на будущее.", 
                               "fail": None, 
                               "food": self.food//2, "health": 0, "morale": 15}},
                    {"text": "Сохранить большую часть (для следующего рейса, +5% боевого духа)", 
                     "effect": {"success": "Вы сохранили большую часть груза для следующего рейса.", 
                               "fail": None, 
                               "food": int(self.food*0.8), "health": 0, "morale": 5}}
                ]
            }
        ]
    
    def load_history_facts(self):
        self.history_facts = [
            {
                'text': "Блокада Ленинграда длилась с 8 сентября 1941 года по 27 января 1944 года (872 дня). Это самая продолжительная и разрушительная блокада в истории человечества.",
                'image': 'history1',
                'sound': None
            },
            {
                'text': "Дорога жизни - ледовая трасса через Ладожское озеро. Зимой 1941-1942 по ней доставляли 2000 тонн грузов ежедневно. Каждый рейс был смертельно опасен.",
                'image': 'history2',
                'sound': None
            },
            {
                'text': "Норма хлеба для рабочих в ноябре 1941 года составляла 250 грамм в день, для остальных - 125 грамм. Люди умирали от голода прямо на улицах.",
                'image': 'history3',
                'sound': None
            }
        ]

    def run(self):
        while self.is_running:
            self.handle_player_input()
            self.draw()
    
    def handle_player_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_r and self.state in (GAME_OVER, VICTORY):
                    self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_click(event.pos)

    def draw(self):
        if self.state == MENU:
            self.draw_menu()
        elif self.state == DAY_START:
            self.draw_day_start()
        elif self.state == GAME:
            self.draw_game()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        elif self.state == VICTORY:
            self.draw_victory()
        elif self.state == HISTORY_FACT:
            self.draw_history_fact()
        elif self.state == SHOW_RESULT:
            self.draw_result()
        
        pygame.display.flip()
        self.fps_clock.tick(MAX_FPS)
    
    def handle_click(self, pos):
        if self.state == MENU:
            if WIDTH//2 - 150 <= pos[0] <= WIDTH//2 + 150 and HEIGHT//2 <= pos[1] <= HEIGHT//2 + 50:
                self.start_game()
        
        elif self.state == DAY_START:
            if WIDTH//2 - 150 <= pos[0] <= WIDTH//2 + 150 and HEIGHT//2 + 100 <= pos[1] <= HEIGHT//2 + 150:
                self.start_day()
        
        elif self.state == GAME and self.waiting_for_choice and self.choices:
            for i in range(len(self.choices)):
                btn_rect = pygame.Rect(WIDTH//4, HEIGHT//2 + i * 90, WIDTH//2, 80)
                if btn_rect.collidepoint(pos):
                    self.process_choice(i)
                    break
        
        elif self.state == HISTORY_FACT:
            if WIDTH//2 - 100 <= pos[0] <= WIDTH//2 + 100 and HEIGHT - 100 <= pos[1] <= HEIGHT - 50:
                self.state = DAY_START
        
        elif self.state == SHOW_RESULT:
            if WIDTH//2 - 150 <= pos[0] <= WIDTH//2 + 150 and HEIGHT - 200 <= pos[1] <= HEIGHT - 150:
                self.next_scene()
                self.check_game_state()
    
    def start_game(self):
        self.day = 1
        self.food = 0
        self.health = 100
        self.morale = 100
        self.ice_stability = 100
        self.date = BLOCKADE_START
        self.state = DAY_START
        self.story_progress = 0
        self.history_facts_shown = []  # Сброс показанных фактов
    
    def start_day(self):
        self.state = GAME
        self.story_progress = (self.day - 1) * 2  # 2 сцены на день
        if self.story_progress >= len(self.story_scenes):
            self.story_progress = len(self.story_scenes) - 1
        self.current_scene = self.story_scenes[self.story_progress]
        self.choices = self.current_scene['choices']
        self.waiting_for_choice = True
    
    def process_choice(self, choice_index):
        if not self.waiting_for_choice or choice_index >= len(self.choices):
            return
            
        choice = self.choices[choice_index]
        effect = choice['effect']
        
        self.waiting_for_choice = False
        
        # Обработка выбора без риска
        if 'risk' not in effect:
            self.result_text = effect['success']
            self.food = max(0, self.food + effect.get('food', 0))
            self.health = max(0, min(100, self.health + effect.get('health', 0)))
            self.morale = max(0, min(100, self.morale + effect.get('morale', 0)))
            self.state = SHOW_RESULT
            return
        
        # Обработка рискованного выбора
        if random.random() > effect['risk']:
            self.result_text = effect['success']
            # Награда за успех
            self.health = min(100, self.health + 10)
            self.morale = min(100, self.morale + 10)
        else:
            self.result_text = effect['fail']
            self.food = max(0, self.food - int(self.food * effect['food_loss']))
            self.health = max(0, self.health - effect['health_loss'])
        
        self.state = SHOW_RESULT
    
    def next_scene(self):
        self.story_progress += 1
        
        # Если сцены закончились, завершаем день
        if self.story_progress >= len(self.story_scenes) or not self.story_scenes[self.story_progress]['text'].startswith(f"День {self.day}"):
            self.end_day()
        else:
            self.current_scene = self.story_scenes[self.story_progress]
            self.choices = self.current_scene['choices']
            self.waiting_for_choice = True
            self.state = GAME
    
    def end_day(self):
        self.day += 1
        self.date += timedelta(days=1)
        
        if self.day > self.max_days:
            self.state = VICTORY
        else:
            self.show_history_fact()
    
    def show_history_fact(self):
        available_facts = [f for f in self.history_facts if f not in self.history_facts_shown]
        if available_facts:
            self.current_history_fact = random.choice(available_facts)
            self.history_facts_shown.append(self.current_history_fact)
            self.state = HISTORY_FACT
        else:
            self.history_facts_shown = []
            self.show_history_fact()
    
    def check_game_state(self):
        if self.health <= 0:
            self.game_over("Ваше здоровье ухудшилось слишком сильно...")
        elif self.morale <= 0:
            self.game_over("Вы потеряли волю к продолжению...")
        elif self.ice_stability <= 0:
            self.game_over("Лёд стал слишком опасным для движения...")
    
    def game_over(self, reason):
        self.state = GAME_OVER
        self.game_over_reason = reason
    
    def draw_menu(self):
        screen.blit(self.images['menu_bg'], (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        Text(
            origin=(WIDTH//2, HEIGHT//4),
            font=font_large,
            text="ДОРОГА ЖИЗНИ",
            color=GOLD
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//4 + 50),
            font=font_medium,
            text="Блокада Ленинграда 1941-1944",
            color=WHITE
        ).draw()

        Button(
            rect=pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 50),
            fill_color=DARK_RED,
            outline_width=2,
            outline_color=BLACK
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2),
            width=300,
            font=font_medium,
            text="НАЧАТЬ ИГРУ",
            color=WHITE
        ).draw()
    
    def draw_day_start(self):
        screen.blit(self.images['scene1'], (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        Text(
            origin=(WIDTH//2, HEIGHT//3),
            font=font_large,
            text=f"ДЕНЬ {self.day}",
            color=GOLD
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2),
            font=font_medium,
            text=self.date.strftime("%d.%m.%Y"),
            color=WHITE
        ).draw()
        Button(
            rect=pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 100, 300, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2 + 100),
            width=300,
            font=font_medium,
            text="НАЧАТЬ ДЕНЬ",
            color=WHITE
        ).draw()
    
    def draw_game(self):
        if self.current_scene and 'image' in self.current_scene:
            screen.blit(self.images[self.current_scene['image']], (0, 0))
        else:
            screen.fill(GRAY)
        
        text_bg = pygame.Surface((WIDTH - 40, HEIGHT//3), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (20, 20))
        
        if self.current_scene:
            Text(
                origin=(50, 30),
                width=WIDTH - 100,
                font=font_small,
                text=self.current_scene['text'],
                color=WHITE,
                should_center=False
            ).draw()
        
        self.draw_status_bar()
        
        if self.waiting_for_choice and self.choices:
            for i, choice in enumerate(self.choices):
                Button(
                    rect=pygame.Rect(WIDTH//4, HEIGHT//2 + i * 90, WIDTH//2, 80),
                    fill_color=DARK_RED if i % 2 == 0 else BLUE,
                    outline_width=2,
                    outline_color=BLACK
                ).draw()
                Text(
                    origin=(WIDTH//2, HEIGHT//2 + i * 90),
                    width=WIDTH//2,
                    font=font_small,
                    text=choice['text'],
                    color=WHITE
                ).draw()
    
    def draw_result(self):
        if self.current_scene and 'image' in self.current_scene:
            screen.blit(self.images[self.current_scene['image']], (0, 0))
        else:
            screen.fill(GRAY)
        
        text_bg = pygame.Surface((WIDTH - 40, HEIGHT//3), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (20, 20))
        
        Text(
            origin=(50, 30),
            width=WIDTH - 100,
            font=font_small,
            text=self.result_text,
            color=WHITE,
            should_center=False
        ).draw()
        
        self.draw_status_bar()
        
        Button(
            rect=pygame.Rect(WIDTH//2 - 150, HEIGHT - 200, 300, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT - 200),
            font=font_medium,
            text="ПРОДОЛЖИТЬ",
            color=WHITE
        ).draw()
    
    def draw_status_bar(self):
        pygame.draw.rect(screen, BLACK, (0, HEIGHT - 80, WIDTH, 80))
        
        # Адаптивные размеры для полосок
        bar_width = WIDTH // 6
        bar_height = 15
        bar_y = HEIGHT - 40
        
        Text(
            origin=(20, HEIGHT - 70),
            text=self.date.strftime('%d.%m.%Y'),
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        Text(
            origin=(20, HEIGHT - 40),
            text=f"День: {self.day}/{self.max_days}",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()

        Text(
            origin=(20, HEIGHT - 40),
            text=f"День: {self.day}/{self.max_days}",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        
        food_x = bar_width
        Text(
            origin=(food_x, HEIGHT - 70),
            text=f"Продовольствие: {self.food} кг",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (food_x, bar_y, bar_width - 20, bar_height))
        food_value = min(1.0, self.food / 250)  # Ограничение до 100%
        pygame.draw.rect(screen, GOLD, (food_x, bar_y, (bar_width - 20) * food_value, bar_height))
        
        health_x = bar_width * 2
        Text(
            origin=(health_x, HEIGHT - 70),
            text=f"Здоровье: {self.health}%",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (health_x, bar_y, bar_width - 20, bar_height))
        health_color = (0, 255, 0) if self.health > 50 else (255, 165, 0) if self.health > 25 else (255, 0, 0)
        health_value = self.health / 100
        pygame.draw.rect(screen, health_color, (health_x, bar_y, (bar_width - 20) * health_value, bar_height))
        
        morale_x = bar_width * 3
        Text(
            origin=(morale_x, HEIGHT - 70),
            text=f"Боевой дух: {self.morale}%",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (morale_x, bar_y, bar_width - 20, bar_height))
        morale_value = self.morale / 100
        pygame.draw.rect(screen, BLUE, (morale_x, bar_y, (bar_width - 20) * morale_value, bar_height))
    
    def draw_history_fact(self):
        screen.blit(self.images[self.current_history_fact['image']], (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        Text(
            origin=(WIDTH//2, 50),
            text="ИСТОРИЧЕСКАЯ СПРАВКА",
            font=font_large,
            color=GOLD
        ).draw()

        Text(
            origin=(50, 150),
            width=WIDTH - 100,
            text=self.current_history_fact['text'],
            font=font_historical,
            color=WHITE,
            should_center=False
        ).draw()

        Button(
            rect=pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT - 100),
            text="ПРОДОЛЖИТЬ",
            font=font_medium,
            color=WHITE,
            should_center=True
        ).draw()
    
    def draw_game_over(self):
        screen.fill(BLACK)
        
        Text(
            origin=(WIDTH//2, HEIGHT//3),
            text="ИГРА ОКОНЧЕНА",
            font=font_large,
            color=RED
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2),
            text=self.game_over_reason,
            font=font_medium,
            color=WHITE
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2 + 100),
            text="Нажмите R для перезапуска",
            font=font_medium,
            color=WHITE
        ).draw()
    
    def draw_victory(self):
        screen.fill(BLUE)
        
        Text(
            origin=(WIDTH//2, HEIGHT//3),
            text="ПОБЕДА!",
            font=font_large,
            color=RED
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2),
            text=f"Вы продержались {self.max_days} дней!",
            font=font_medium,
            color=WHITE
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2 + 50),
            text="Ваши усилия помогли спасти жизни ленинградцев.",
            font=font_medium,
            color=WHITE
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2 + 100),
            text="Нажмите R для перезапуска",
            font=font_medium,
            color=WHITE
        ).draw()
    
    def reset_game(self):
        self.__init__()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()