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

# Ограничение параметров
MAX_FOOD = 250
MAX_HEALTH = 100
MAX_MORALE = 100

# 
@dataclasses.dataclass
class PlayerStats:
    """Этот класс описывает параметры игрока."""
    food: int
    """Текущее количество еды."""
    health: int
    """Текущее количество здоровья."""
    morale: int
    """Текущее количество боевого духа."""

@dataclasses.dataclass
class PlayerStatsModifier:
    """Этот класс описывает изменение параметров игрока из-за внешних факторов."""
    food: int
    """Изменение в количестве еды."""
    health: int
    """Изменение в количестве здоровья."""
    morale: int
    """Изменение в количестве боевого духа."""

    def apply(self, stats: PlayerStats):
        stats.food = max(min(self.food + stats.food, MAX_FOOD), 0)
        stats.health = max(min(self.health + stats.health, MAX_HEALTH), 0)
        stats.morale = max(min(self.morale + stats.morale, MAX_MORALE), 0)

@dataclasses.dataclass
class SimpleConsequence:
    """Этот класс описывает последствия обычного выбора."""
    text: str
    """Текст, описывающий последствия выбора."""
    modifier: PlayerStatsModifier
    """Изменение параметров происходящее происходящее в результате выбора."""

    def apply_consequences(self, stats: PlayerStats) -> str:
        """Применяет последствия выбора к параметрам игрока. 
        
        Возвращает текст, описывающий последствия выбора."""
        self.modifier.apply(stats)
        return self.text

@dataclasses.dataclass
class RiskBasedConsequence:
    """Этот класс описывает последствия выбора, связанного с риском."""
    risk: float
    """Шанс успеха в промежутке от 1 до 0."""
    success: SimpleConsequence
    """Последствия при успехе."""
    failure: SimpleConsequence
    """Последствия при провале."""

    def apply_consequences(self, stats: PlayerStats) -> str:
        """Применяет последствия выбора к параметрам игрока. 
        
        Возвращает текст, описывающий последствия выбора."""
        if random.random() > self.risk:
            return self.success.apply_consequences(stats)
        else:
            return self.failure.apply_consequences(stats)

@dataclasses.dataclass
class Choice:
    """Этот класс описывает выбор."""
    text: str
    """Текст выбора."""
    consequence: SimpleConsequence | RiskBasedConsequence
    """Последствие выбора."""

@dataclasses.dataclass
class Scene:
    """Этот класс описывает сцену (этап игры с выборами)."""
    text: str
    """Текскт описывающий сцену."""
    background: pygame.Surface
    """Фоновое изображение сцены."""
    sound: pygame.mixer.Sound
    """Звук играющий при начале сцены."""
    choices: list[Choice]
    """Список выборов доступных в сцене."""

@dataclasses.dataclass
class Button:
    """Этот класс описывает кнопку на экране (без текста)."""
    rect: pygame.Rect
    """Прямоугольник кнопки."""
    fill_color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(WHITE))
    """Цвет заливки."""
    outline_width: int = 0
    """Ширина обводки."""
    outline_color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(WHITE))
    """Цвет обводки."""

    def draw(self):
        """Отрисовывает кнопку на экране."""
        pygame.draw.rect(screen, self.fill_color, self.rect)
        pygame.draw.rect(screen, self.outline_color, self.rect, self.outline_width)
    
    def contains_point(self, point: tuple[int, int]) -> bool:
        """Проверяет находится ли курсор внутри кнопки."""
        return self.rect.collidepoint(point)

@dataclasses.dataclass
class Text:
    """Этот класс описывает текст на экране."""
    origin: tuple[int, int]
    """Точка - основание текста."""
    font: pygame.font.Font
    """Шрифт текста."""
    text: str = "Это Текст!"
    """Текст."""
    width: int = -1
    """Ширина по которой разделять текст на отдельные строки.
    
    Если это значение меньше нуля, то ширина текста не влияет на разделение по строкам."""
    color: pygame.Color = dataclasses.field(default_factory=lambda: pygame.Color(BLACK))
    """Цвет текста."""
    should_center: bool = True
    """Нужно ли центрировать текст относительно его основания."""

    def draw(self):
        """отрисовывает текст на экран"""
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
        """разбивает текст на отдельные строки"""
        newlines = self.text.split('\n')

        lines = []
        current_line = []
        
        for newline in newlines:
            if self.width <= 0:
                lines.append(newline)
                continue
            
            for word in newline.split(' '):
                test_line = ' '.join(current_line + [word])
                test_width = self.font.size(test_line)[0]
                
                if test_width < self.width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
                current_line = []
        
        
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
        self.stats: PlayerStats
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
            Scene(
                text=f"День 1. {self.date.strftime('%d.%m.%Y')}\nВы загружаете грузовик на базе. Сколько продовольствия взять?",
                background=self.create_image((80, 80, 100)),  # grey
                sound=None,
                choices=[
                    Choice(
                        text="Максимальный груз (250 кг, риск провалиться под лёд)",
                        consequence=SimpleConsequence(
                            text="Вы загрузили максимальный груз. Будьте осторожны!",
                            modifier=PlayerStatsModifier(250, -20, -10)
                        )
                    ),
                    Choice(
                        text="Средний груз (150 кг, баланс риска и пользы)",
                        consequence=SimpleConsequence(
                            text="Вы загрузили средний груз. Разумный выбор.",
                            modifier=PlayerStatsModifier(150, -10, -5)
                        )
                    ),
                    Choice(
                        text="Минимальный груз (50 кг, безопасно, но мало еды)",
                        consequence=SimpleConsequence(
                            "Вы взяли минимальный груз. Городу будет тяжело...",
                            PlayerStatsModifier(50, 0, 0)
                        )
                    )
                ]
            ),
            Scene(
                text="День 1. Вы движетесь по льду Ладожского озера. Впереди трещина во льду. Что делать?",
                background=self.create_image((70, 90, 80)),  # cold
                sound=None,
                choices=[
                    Choice(
                        text="Проехать быстро (риск провалиться)",
                        consequence=RiskBasedConsequence(
                            risk=0.4, 
                            success=SimpleConsequence(
                                text="Вы успешно проехали трещину на скорости!",
                                modifier=PlayerStatsModifier(0, 10, 10)
                            ), 
                            failure=SimpleConsequence(
                                text="Грузовик провалился под лёд! Вы потеряли весь груз.",
                                modifier=PlayerStatsModifier(-250, -30, 0)
                            )
                        )
                    ),
                    Choice(
                        text="Проехать медленно (безопаснее)",
                        consequence=RiskBasedConsequence(
                            risk=0.2, 
                            success=SimpleConsequence(
                                text="Вы осторожно пересекли трещину.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ),
                            failure=SimpleConsequence(
                                text="Лёд треснул, но вы успели проехать! Часть груза повреждена.",
                                modifier=PlayerStatsModifier(30, -10, 0)
                            )
                        )
                    ),
                    Choice(
                        text="Объехать (потеря времени, -10% боевого духа)",
                        consequence=SimpleConsequence(
                            text="Вы выбрали безопасный путь, потеряв время.",
                            modifier=PlayerStatsModifier(0, 0, -10)
                        )
                    )
                ]
            ),
            Scene(
                text=f"День 2. {(self.date + timedelta(days=1)).strftime('%d.%m.%Y')}\nВ небе появляются немецкие самолёты!",
                background=self.create_image((90, 60, 70)),  # red
                sound=None,
                choices=[
                    Choice(
                        text="Ускориться и попытаться уехать",
                        consequence=RiskBasedConsequence(
                            risk=0.5,
                            success=SimpleConsequence(
                                text="Вам удалось уйти от бомбёжки!",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ), 
                            failure=SimpleConsequence(
                                text="Прямое попадание! Грузовик уничтожен.",
                                modifier=PlayerStatsModifier(-250, -50, 0)
                            )
                        )
                    ),
                    Choice(
                        text="Остановиться и замаскироваться",
                        consequence=RiskBasedConsequence(
                            risk=0.3,
                            success=SimpleConsequence(
                                text="Самолёты вас не заметили.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ), 
                            failure=SimpleConsequence(
                                text="Бомбы упали рядом, грузовик повреждён.",
                                modifier=PlayerStatsModifier(-50, -20, 0)
                            )
                        )
                    ),
                    Choice(
                        text="Продолжить движение как есть",
                        consequence=RiskBasedConsequence(
                            risk=0.7,
                            success=SimpleConsequence(
                                text="Самолёты пролетели мимо.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ), 
                            failure=SimpleConsequence(
                                text="Бомба попала в грузовик!",
                                modifier=PlayerStatsModifier(-0.8 * 250, -40, 0)
                            )
                        )
                    ),
                ]
            ),
            Scene(
                text=f"День 3. {(self.date + timedelta(days=2)).strftime('%d.%m.%Y')}\nВы встретили колонну грузовиков. Командир предлагает объединиться.",
                background=self.create_image((60, 80, 90)),  # unknown?
                sound=None,
                choices=[
                    Choice(
                        text="Присоединиться к колонне (+10% боевого духа)",
                        consequence=SimpleConsequence(
                            text="Вы присоединились к колонне. Движение безопаснее.",
                            modifier=PlayerStatsModifier(0, 0, 10),
                        )
                    ),
                    Choice(
                        text="Продолжить самостоятельно (риск нападения)",
                        consequence=RiskBasedConsequence(
                            risk=0.3,
                            success=SimpleConsequence(
                                text="Вы благополучно доехали одни.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ),
                            failure=SimpleConsequence(
                                text="На вас напали! Часть груза украдена.",
                                modifier=PlayerStatsModifier(-0.4 * 250, -15, 0)
                            )
                        )
                    )
                ]
            ),
            Scene(
                text=f"День 4. {(self.date + timedelta(days=3)).strftime('%d.%m.%Y')}\nНачалась сильная метель! Видимость практически нулевая.",
                background=self.create_image((60, 80, 90)),  # blue, snow storm
                sound=None,
                choices=[
                    Choice(
                        text="Остановиться и переждать (потеря времени, -10 кг продовольствия)",
                        consequence=SimpleConsequence(
                            text="Вы переждали метель, потеряв немного времени.",
                            modifier=PlayerStatsModifier(-10, 0, 0)
                        )
                    ),
                    Choice(
                        text="Продолжить движение (высокий риск аварии)",
                        consequence=RiskBasedConsequence(
                            risk=0.6,
                            success=SimpleConsequence(
                                text="Вы благополучно преодолели метель.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ),
                            failure=SimpleConsequence(
                                text="Вы съехали с трассы! Грузовик застрял.",
                                modifier=PlayerStatsModifier(-0.5 * 250, -20, 0)
                            )
                        )
                    )
                ]
            ),
            Scene(
                text=f"День 5. {(self.date + timedelta(days=4)).strftime('%d.%m.%Y')}\nВы прибыли в Ленинград. Голодные жители смотрят на ваш грузовик.",
                background=self.create_image((90, 70, 80)),  # warm, city
                sound=None,
                choices=[
                    Choice(
                        text="Раздать всё продовольствие (+30% боевого духа)",
                        consequence=SimpleConsequence(
                            text="Вы раздали весь груз. Люди благодарны вам!",
                            modifier=PlayerStatsModifier(0, 0, 30)
                        )
                    ),
                    Choice(
                        text="Раздать половину (остальное на следующий рейс, +15% боевого духа)",
                        consequence=SimpleConsequence(
                            text="Вы раздали половину груза, сохранив часть на будущее.",
                            modifier=PlayerStatsModifier(50, 0, 15)
                        )
                    ),
                    Choice(
                        text="Сохранить большую часть (для следующего рейса, +5% боевого духа)",
                        consequence=SimpleConsequence(
                            text="Вы сохранили большую часть груза для следующего рейса.",
                            modifier=PlayerStatsModifier(-20, 0, 5)
                        )
                    )
                ]
            )
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
        self.stats = PlayerStats(0, 100, 100)
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
        self.choices = self.current_scene.choices
        self.waiting_for_choice = True
    
    def process_choice(self, choice_index):
        if not self.waiting_for_choice or choice_index >= len(self.choices):
            return
        
        self.waiting_for_choice = False
        self.result_text = self.choices[choice_index].consequence.apply_consequences(self.stats)
        
        self.state = SHOW_RESULT
    
    def next_scene(self):
        self.story_progress += 1
        
        # Если сцены закончились, завершаем день
        if self.story_progress >= len(self.story_scenes) or not self.story_scenes[self.story_progress].text.startswith(f"День {self.day}"):
            self.end_day()
        else:
            self.current_scene = self.story_scenes[self.story_progress]
            self.choices = self.current_scene.choices
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
        if self.stats.health <= 0:
            self.game_over("Ваше здоровье ухудшилось слишком сильно...")
        elif self.stats.morale <= 0:
            self.game_over("Вы потеряли волю к продолжению...")
        # elif self.ice_stability <= 0:
        #     self.game_over("Лёд стал слишком опасным для движения...")
    
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
        if self.current_scene and self.current_scene.background:
            screen.blit(self.current_scene.background, (0, 0))
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
                text=self.current_scene.text,
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
                    text=choice.text,
                    color=WHITE
                ).draw()
    
    def draw_result(self):
        if self.current_scene and self.current_scene.background:
            screen.blit(self.current_scene.background, (0, 0))
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
            text=f"Продовольствие: {self.stats.food} кг",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (food_x, bar_y, bar_width - 20, bar_height))
        food_value = min(1.0, self.stats.food / 250)  # Ограничение до 100%
        pygame.draw.rect(screen, GOLD, (food_x, bar_y, (bar_width - 20) * food_value, bar_height))
        
        health_x = bar_width * 2
        Text(
            origin=(health_x, HEIGHT - 70),
            text=f"Здоровье: {self.stats.health}%",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (health_x, bar_y, bar_width - 20, bar_height))
        health_color = (0, 255, 0) if self.stats.health > 50 else (255, 165, 0) if self.stats.health > 25 else (255, 0, 0)
        health_value = self.stats.health / 100
        pygame.draw.rect(screen, health_color, (health_x, bar_y, (bar_width - 20) * health_value, bar_height))
        
        morale_x = bar_width * 3
        Text(
            origin=(morale_x, HEIGHT - 70),
            text=f"Боевой дух: {self.stats.morale}%",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        pygame.draw.rect(screen, GRAY, (morale_x, bar_y, bar_width - 20, bar_height))
        morale_value = self.stats.morale / 100
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
            text=self.game_over_reason + '\n' +
                 "Нажмите R для перезапуска",
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
            text=f"Вы продержались {self.max_days} дней!\n" +
                 "Ваши усилия помогли спасти жизни ленинградцев.\n" +
                 "Нажмите R для перезапуска",
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