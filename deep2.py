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
GREEN = pygame.Color(50, 150, 50)

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
SCENE_START = 6

# Исторические даты блокады
BLOCKADE_START = datetime(1941, 9, 8)
BLOCKADE_END = datetime(1944, 1, 27)

# Ограничение частоты кадров
MAX_FPS = 30

# Ограничение параметров
MAX_FOOD = 250
MAX_HEALTH = 100
MAX_MORALE = 100
MIN_HEALTH_CRITICAL = 20
MIN_MORALE_CRITICAL = 20

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
    total_delivered: int = 0
    """Общее доставленное продовольствие"""
    evacuated: int = 0
    """Количество эвакуированных людей"""

@dataclasses.dataclass
class PlayerStatsModifier:
    """Этот класс описывает изменение параметров игрока из-за внешних факторов."""
    food: int = 0
    """Изменение в количестве еды."""
    health: int = 0
    """Изменение в количестве здоровья."""
    morale: int = 0
    """Изменение в количестве боевого духа."""
    delivered: int = 0
    """Доставленное продовольствие"""
    evacuated: int = 0
    """Эвакуированные люди"""

    def apply(self, stats: PlayerStats):
        stats.food = max(min(self.food + stats.food, MAX_FOOD), 0)
        stats.health = max(min(self.health + stats.health, MAX_HEALTH), 0)
        stats.morale = max(min(self.morale + stats.morale, MAX_MORALE), 0)
        stats.total_delivered += self.delivered
        stats.evacuated += self.evacuated

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
        if random.random() < self.risk:
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
    title: str
    """Заголовок сцены"""
    text: str
    """Текскт описывающий сцену."""
    background: pygame.Surface
    """Фоновое изображение сцены."""
    sound: pygame.mixer.Sound
    """Звук играющий при начале сцены."""
    choices: list[Choice]
    """Список выборов доступных в сцене."""
    date: datetime
    """Дата события"""

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
        self.stats: PlayerStats
        self.scene_index = 0
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
        self.menu_background = self.create_image((50, 70, 90))  # Темно-синий
        self.scene_start_background = self.create_image((80, 80, 100))
    
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
        # Исторически обоснованная сюжетная линия
        self.story_scenes = [
            # Формирование "Дороги жизни"
            Scene(
                title="Начало блокады",
                text="Сентябрь 1941 года. Немецкие войска замкнули кольцо вокруг Ленинграда.\n"
                     "Вы - водитель грузовика, которому поручено проложить путь через Ладожское озеро.\n"
                     "Какой груз взять для первого рейса?",
                background=self.create_image((80, 80, 100)),
                sound=None,
                date=datetime(1941, 9, 12),
                choices=[
                    Choice(
                        text="Максимальный груз (250 кг муки)",
                        consequence=SimpleConsequence(
                            text="Вы загрузили максимальный груз. Будьте осторожны на тонком льду!",
                            modifier=PlayerStatsModifier(250, -15, -10)
                        )
                    ),
                    Choice(
                        text="Средний груз (150 кг, баланс)",
                        consequence=SimpleConsequence(
                            text="Вы загрузили средний груз. Разумный выбор для первого рейса.",
                            modifier=PlayerStatsModifier(150, -5, 0)
                        )
                    ),
                    Choice(
                        text="Минимальный груз (50 кг, для разведки пути)",
                        consequence=SimpleConsequence(
                            "Вы взяли минимальный груз. Город ждет продовольствия...",
                            PlayerStatsModifier(50, 5, -5)
                        )
                    )
                ]
            ),
            
            # Первые рейсы по льду
            Scene(
                title="Ледовая трасса",
                text="Ноябрь 1941 года. Лед на Ладожском озере окреп.\n"
                     "Вы везете муку в осажденный город. Впереди трещина во льду.\n"
                     "Как преодолеть опасный участок?",
                background=self.create_image((70, 90, 80)),
                sound=None,
                date=datetime(1941, 11, 20),
                choices=[
                    Choice(
                        text="Проехать быстро (риск провалиться)",
                        consequence=RiskBasedConsequence(
                            risk=0.4, 
                            success=SimpleConsequence(
                                text="Вы успешно проехали трещину на скорости!",
                                modifier=PlayerStatsModifier(0, -5, 10)
                            ), 
                            failure=SimpleConsequence(
                                text="Грузовик провалился под лёд! Вы потеряли весь груз.",
                                modifier=PlayerStatsModifier(-250, -30, -20)
                            )
                        )
                    ),
                    Choice(
                        text="Проехать медленно (осторожно)",
                        consequence=RiskBasedConsequence(
                            risk=0.2, 
                            success=SimpleConsequence(
                                text="Вы осторожно пересекли трещину.",
                                modifier=PlayerStatsModifier(0, 0, 0)
                            ),
                            failure=SimpleConsequence(
                                text="Лёд треснул, но вы успели проехать! Часть груза повреждена.",
                                modifier=PlayerStatsModifier(-50, -15, -10)
                            )
                        )
                    ),
                    Choice(
                        text="Объехать (потеря времени)",
                        consequence=SimpleConsequence(
                            text="Вы выбрали безопасный путь, потеряв драгоценное время.",
                            modifier=PlayerStatsModifier(0, 0, -10)
                        )
                    )
                ]
            ),
            
            # Бомбардировки трассы
            Scene(
                title="Воздушные налеты",
                text="Декабрь 1941 года. Немецкая авиация постоянно бомбит трассу.\n"
                     "В небе появились вражеские самолеты. Ваши действия?",
                background=self.create_image((90, 60, 70)),
                sound=None,
                date=datetime(1941, 12, 15),
                choices=[
                    Choice(
                        text="Ускориться и попытаться уехать",
                        consequence=RiskBasedConsequence(
                            risk=0.5,
                            success=SimpleConsequence(
                                text="Вам удалось уйти от бомбёжки!",
                                modifier=PlayerStatsModifier(0, -5, 5)
                            ), 
                            failure=SimpleConsequence(
                                text="Прямое попадание! Грузовик уничтожен.",
                                modifier=PlayerStatsModifier(-250, -40, -30)
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
                                modifier=PlayerStatsModifier(-50, -20, -15)
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
                                modifier=PlayerStatsModifier(-100, -30, -20)
                            )
                        )
                    ),
                ]
            ),
            
            # Голод в Ленинграде
            Scene(
                title="Хлеб блокадного города",
                text="Январь 1942 года. Вы прибыли в Ленинград. На разгрузке к вам подошли истощенные дети.\n"
                     "Они просят еды. Ваши действия?",
                background=self.create_image((60, 60, 70)),
                sound=None,
                date=datetime(1942, 1, 20),
                choices=[
                    Choice(
                        text="Отдать свой паек (-20 кг еды)",
                        consequence=SimpleConsequence(
                            text="Дети благодарны вам. Вы чувствуете, что поступили правильно.",
                            modifier=PlayerStatsModifier(-20, 0, 15)
                        )
                    ),
                    Choice(
                        text="Отказать (выполняя приказ)",
                        consequence=SimpleConsequence(
                            text="Вы не смогли смотреть в глаза детям...",
                            modifier=PlayerStatsModifier(0, 0, -10)
                        )
                    ),
                    Choice(
                        text="Отдать часть груза (-50 кг, рискуя наказанием)",
                        consequence=RiskBasedConsequence(
                            risk=0.6,
                            success=SimpleConsequence(
                                text="Командир одобрил ваш поступок.",
                                modifier=PlayerStatsModifier(-50, 0, 20)
                            ),
                            failure=SimpleConsequence(
                                text="Вас наказали за самовольное решение.",
                                modifier=PlayerStatsModifier(0, -10, -15)
                            )
                        )
                    )
                ]
            ),
            
            # Эвакуация жителей
            Scene(
                title="Обратный путь",
                text="Февраль 1942 года. В обратный путь нужно взять эвакуированных.\n"
                     "Сколько людей вы готовы взять?",
                background=self.create_image((50, 60, 70)),
                sound=None,
                date=datetime(1942, 2, 10),
                choices=[
                    Choice(
                        text="Максимум (5 человек, риск перегруза)",
                        consequence=RiskBasedConsequence(
                            risk=0.7,
                            success=SimpleConsequence(
                                text="Вы благополучно доставили людей!",
                                modifier=PlayerStatsModifier(0, -10, 15, evacuated=5)
                            ),
                            failure=SimpleConsequence(
                                text="Грузовик провалился под лёд!",
                                modifier=PlayerStatsModifier(-100, -30, -20, evacuated=-5)
                            )
                        )
                    ),
                    Choice(
                        text="3 человека (баланс)",
                        consequence=SimpleConsequence(
                            text="Вы доставили людей без происшествий.",
                            modifier=PlayerStatsModifier(0, 0, 10, evacuated=3)
                        )
                    ),
                    Choice(
                        text="Никого не брать (строго по приказу)",
                        consequence=SimpleConsequence(
                            text="Вы уехали без пассажиров...",
                            modifier=PlayerStatsModifier(0, 0, -15)
                        )
                    )
                ]
            ),
            
            # Весенняя распутица
            Scene(
                title="Таяние льда",
                text="Апрель 1942 года. Лед на озере становится тонким.\n"
                     "Нужно доставить последний груз по зимней дороге. Ваше решение?",
                background=self.create_image((70, 100, 120)),
                sound=None,
                date=datetime(1942, 4, 5),
                choices=[
                    Choice(
                        text="Рискнуть и поехать (последний шанс)",
                        consequence=RiskBasedConsequence(
                            risk=0.3,
                            success=SimpleConsequence(
                                text="Вы успешно доставили груз по тающему льду!",
                                modifier=PlayerStatsModifier(150, -15, 20, delivered=150)
                            ),
                            failure=SimpleConsequence(
                                text="Грузовик провалился под лёд!",
                                modifier=PlayerStatsModifier(-150, -30, -25)
                            )
                        )
                    ),
                    Choice(
                        text="Дождаться кораблей (потеря времени)",
                        consequence=SimpleConsequence(
                            text="Вы дождались навигации, но город терял людей каждый день...",
                            modifier=PlayerStatsModifier(0, 0, -10)
                        )
                    ),
                    Choice(
                        text="Искать обходной путь (неизвестный маршрут)",
                        consequence=RiskBasedConsequence(
                            risk=0.5,
                            success=SimpleConsequence(
                                text="Вы нашли безопасный путь!",
                                modifier=PlayerStatsModifier(100, -5, 10, delivered=100)
                            ),
                            failure=SimpleConsequence(
                                text="Вы заблудились и потеряли часть груза.",
                                modifier=PlayerStatsModifier(-50, -10, -15)
                            )
                        )
                    )
                ]
            ),
            
            # Летние перевозки
            Scene(
                title="Ладьяжская флотилия",
                text="Июль 1942 года. Вы перевозите грузы на барже. Немецкие самолеты атакуют караван.\n"
                     "Ваши действия?",
                background=self.create_image((60, 80, 100)),
                sound=None,
                date=datetime(1942, 7, 15),
                choices=[
                    Choice(
                        text="Маневрировать под огнем",
                        consequence=RiskBasedConsequence(
                            risk=0.4,
                            success=SimpleConsequence(
                                text="Вы умело уклонились от бомб!",
                                modifier=PlayerStatsModifier(0, -10, 15)
                            ),
                            failure=SimpleConsequence(
                                text="Бомба попала в баржу!",
                                modifier=PlayerStatsModifier(-100, -30, -20)
                            )
                        )
                    ),
                    Choice(
                        text="Отстреливаться из зенитки",
                        consequence=RiskBasedConsequence(
                            risk=0.3,
                            success=SimpleConsequence(
                                text="Вы сбили вражеский самолет!",
                                modifier=PlayerStatsModifier(0, 0, 20)
                            ),
                            failure=SimpleConsequence(
                                text="Зенитка повреждена, баржа тонет!",
                                modifier=PlayerStatsModifier(-150, -20, -15)
                            )
                        )
                    ),
                    Choice(
                        text="Выбросить груз за борт (для скорости)",
                        consequence=SimpleConsequence(
                            text="Вы спасли баржу, но потеряли груз...",
                            modifier=PlayerStatsModifier(-100, 0, -20)
                        )
                    )
                ]
            ),
            
            # Вторая блокадная зима
            Scene(
                title="Снова на лед",
                text="Декабрь 1942 года. Снова установился лед. Дорога жизни возобновила работу.\n"
                     "Вы везете продовольствие и медикаменты. Встретили замерзающего солдата.",
                background=self.create_image((40, 60, 80)),
                sound=None,
                date=datetime(1942, 12, 20),
                choices=[
                    Choice(
                        text="Взять с собой (-10 кг груза)",
                        consequence=SimpleConsequence(
                            text="Вы спасли солдата. Он благодарен вам.",
                            modifier=PlayerStatsModifier(-10, 0, 15)
                        )
                    ),
                    Choice(
                        text="Дать еду и теплую одежду (-5 кг груза)",
                        consequence=SimpleConsequence(
                            text="Вы помогли солдату, но оставили его.",
                            modifier=PlayerStatsModifier(-5, 0, 5)
                        )
                    ),
                    Choice(
                        text="Проехать мимо (выполняя приказ)",
                        consequence=SimpleConsequence(
                            text="Вы не остановились...",
                            modifier=PlayerStatsModifier(0, 0, -15)
                        )
                    )
                ]
            ),
            
            # Прорыв блокады
            Scene(
                title="Операция 'Искра'",
                text="Январь 1943 года. Советские войска прорвали блокаду!\n"
                     "Вы везете праздничный груз в Ленинград. Как поступить с грузом?",
                background=self.create_image((90, 70, 80)),
                sound=None,
                date=datetime(1943, 1, 18),
                choices=[
                    Choice(
                        text="Раздать все жителям (+30% морали)",
                        consequence=SimpleConsequence(
                            text="Люди ликуют! Блокада прорвана!",
                            modifier=PlayerStatsModifier(0, 0, 30, delivered=150)
                        )
                    ),
                    Choice(
                        text="Передать на склады (по инструкции)",
                        consequence=SimpleConsequence(
                            text="Вы выполнили приказ. Груз пойдет на организованное распределение.",
                            modifier=PlayerStatsModifier(0, 0, 10, delivered=150)
                        )
                    ),
                    Choice(
                        text="Часть раздать, часть сдать (-100 кг груза)",
                        consequence=SimpleConsequence(
                            text="Вы нашли компромисс между приказом и состраданием.",
                            modifier=PlayerStatsModifier(-100, 0, 20, delivered=50)
                        )
                    )
                ]
            ),
            
            # Полное освобождение
            Scene(
                title="Снятие блокады",
                text="Январь 1944 года. Блокада Ленинграда полностью снята!\n"
                     "Ваш последний рейс. Как завершить свою миссию?",
                background=self.create_image((100, 100, 120)),
                sound=None,
                date=datetime(1944, 1, 27),
                choices=[
                    Choice(
                        text="Везти максимальный груз (честь водителя)",
                        consequence=SimpleConsequence(
                            text="Вы доставили рекордный груз в освобожденный город!",
                            modifier=PlayerStatsModifier(250, -10, 25, delivered=250)
                        )
                    ),
                    Choice(
                        text="Взять ветеранов блокады (5 человек)",
                        consequence=SimpleConsequence(
                            text="Вы доставили героев блокады на торжества.",
                            modifier=PlayerStatsModifier(-50, 0, 30, evacuated=5)
                        )
                    ),
                    Choice(
                        text="Совершить памятный рейс (с символическим грузом)",
                        consequence=SimpleConsequence(
                            text="Ваш рейс стал символом победы над блокадой.",
                            modifier=PlayerStatsModifier(50, 10, 35, delivered=50)
                        )
                    )
                ]
            )
        ]
    
    def load_history_facts(self):
        self.history_facts_background = self.create_image((70, 70, 90))
        self.history_facts = [
            "Блокада Ленинграда длилась 872 дня - с 8 сентября 1941 года по 27 января 1944 года.",
            "Дорога жизни - ледовая трасса через Ладожское озеро. Зимой 1941-1942 по ней доставляли до 2000 тонн грузов ежедневно.",
            "Норма хлеба в ноябре 1941 года: 250 грамм для рабочих, 125 грамм для остальных. Люди умирали от голода на улицах.",
            "За время блокады по Дороге жизни эвакуировали более 1,3 млн человек, в основном женщин и детей.",
            "Температура зимой 1941-1942 опускалась до -32°C. Водители работали по 12-16 часов без отопления в кабинах.",
            "Всего по Дороге жизни в Ленинград доставили более 1,6 млн тонн грузов, что спасло жизни сотен тысяч людей.",
            "Каждый третий рейс заканчивался потерей грузовика - он либо проваливался под лёд, либо уничтожался авиацией.",
            "18 января 1943 года блокада была прорвана в ходе операции 'Искра', но полное освобождение наступило лишь год спустя."
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
        elif self.state == SCENE_START:
            self.draw_scene_start()
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
        
        elif self.state == SCENE_START:
            if WIDTH//2 - 150 <= pos[0] <= WIDTH//2 + 150 and HEIGHT//2 + 100 <= pos[1] <= HEIGHT//2 + 150:
                self.start_scene()
        
        elif self.state == GAME and self.waiting_for_choice and self.choices:
            for i in range(len(self.choices)):
                btn_rect = pygame.Rect(WIDTH//4, HEIGHT//2 + i * 90, WIDTH//2, 80)
                if btn_rect.collidepoint(pos):
                    self.process_choice(i)
                    break
        
        elif self.state == HISTORY_FACT:
            if WIDTH//2 - 100 <= pos[0] <= WIDTH//2 + 100 and HEIGHT - 100 <= pos[1] <= HEIGHT - 50:
                self.state = SCENE_START
        
        elif self.state == SHOW_RESULT:
            if WIDTH//2 - 150 <= pos[0] <= WIDTH//2 + 150 and HEIGHT - 200 <= pos[1] <= HEIGHT - 150:
                self.next_scene()
                self.check_game_state()
    
    def start_game(self):
        self.scene_index = 0
        self.stats = PlayerStats(0, 85, 80)  # Начальные значения ниже максимума
        self.date = BLOCKADE_START
        self.state = SCENE_START
        self.history_facts_shown = []  # Сброс показанных фактов
    
    def start_scene(self):
        self.state = GAME
        self.current_scene = self.story_scenes[self.scene_index]
        self.date = self.current_scene.date
        self.choices = self.current_scene.choices
        self.waiting_for_choice = True
    
    def process_choice(self, choice_index):
        if not self.waiting_for_choice or choice_index >= len(self.choices):
            return
        
        self.waiting_for_choice = False
        self.result_text = self.choices[choice_index].consequence.apply_consequences(self.stats)
        
        # Проверка критических состояний после выбора
        if self.stats.health < MIN_HEALTH_CRITICAL:
            self.result_text += "\n\nВаше здоровье критически низкое!"
        if self.stats.morale < MIN_MORALE_CRITICAL:
            self.result_text += "\n\nВаш боевой дух на нуле!"
            
        self.state = SHOW_RESULT
    
    def next_scene(self):
        self.scene_index += 1
        
        # Если сцены закончились - победа
        if self.scene_index >= len(self.story_scenes):
            self.state = VICTORY
        else:
            self.state = SCENE_START
    
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
        elif self.stats.health < MIN_HEALTH_CRITICAL and random.random() < 0.3:
            self.game_over("Критическое состояние здоровья привело к гибели...")
        elif self.stats.morale < MIN_MORALE_CRITICAL and random.random() < 0.3:
            self.game_over("Потеря боевого духа сделала продолжение невозможным...")
    
    def game_over(self, reason):
        self.state = GAME_OVER
        self.game_over_reason = reason
    
    def draw_menu(self):
        screen.blit(self.menu_background, (0, 0))
        
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
    
    def draw_scene_start(self):
        screen.blit(self.scene_start_background, (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        scene = self.story_scenes[self.scene_index]
        
        Text(
            origin=(WIDTH//2, HEIGHT//4),
            font=font_large,
            text=scene.title,
            color=GOLD
        ).draw()
        
        Text(
            origin=(WIDTH//2, HEIGHT//3),
            font=font_medium,
            text=scene.date.strftime("%d.%m.%Y"),
            color=WHITE
        ).draw()
        
        # Показ статуса игрока
        Text(
            origin=(WIDTH//2, HEIGHT//2 - 50),
            font=font_small,
            text=f"Здоровье: {self.stats.health}% | Боевой дух: {self.stats.morale}%",
            color=WHITE
        ).draw()
        
        Text(
            origin=(WIDTH//2, HEIGHT//2 - 20),
            font=font_small,
            text=f"Доставлено: {self.stats.total_delivered} кг | Эвакуировано: {self.stats.evacuated} чел.",
            color=WHITE
        ).draw()
        
        Button(
            rect=pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        ).draw()
        Text(
            origin=(WIDTH//2, HEIGHT//2 + 50),
            width=300,
            font=font_medium,
            text="НАЧАТЬ СЦЕНУ",
            color=WHITE
        ).draw()
    
    def draw_game(self):
        if self.current_scene and self.current_scene.background:
            screen.blit(self.current_scene.background, (0, 0))
        else:
            screen.fill(GRAY)
        
        # Заголовок и дата
        title_bg = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
        title_bg.fill((0, 0, 0, 200))
        screen.blit(title_bg, (0, 0))
        
        Text(
            origin=(WIDTH//2, 20),
            font=font_medium,
            text=self.current_scene.title,
            color=GOLD
        ).draw()
        
        Text(
            origin=(WIDTH//2, 60),
            font=font_small,
            text=self.current_scene.date.strftime("%d.%m.%Y"),
            color=WHITE
        ).draw()
        
        # Основной текст сцены
        text_bg = pygame.Surface((WIDTH - 40, HEIGHT//3), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (20, 100))
        
        Text(
            origin=(50, 110),
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
                    origin=(WIDTH//2, HEIGHT//2 + i * 90 + 40),
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
        
        text_bg = pygame.Surface((WIDTH - 40, HEIGHT//2), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (20, 100))
        
        Text(
            origin=(50, 110),
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
            text=f"Этап: {self.scene_index+1}/{len(self.story_scenes)}",
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
        
        # Цвет здоровья зависит от уровня
        if self.stats.health > 50:
            health_color = GREEN
        elif self.stats.health > 25:
            health_color = (255, 165, 0)  # оранжевый
        else:
            health_color = RED
            
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
        
        # Цвет морали зависит от уровня
        if self.stats.morale > 60:
            morale_color = BLUE
        elif self.stats.morale > 30:
            morale_color = (100, 100, 255)  # светлосиний
        else:
            morale_color = (150, 150, 255)  # бледно-синий
            
        morale_value = self.stats.morale / 100
        pygame.draw.rect(screen, morale_color, (morale_x, bar_y, (bar_width - 20) * morale_value, bar_height))
        
        # Дополнительная информация
        delivered_x = bar_width * 4
        Text(
            origin=(delivered_x, HEIGHT - 70),
            text=f"Доставлено: {self.stats.total_delivered} кг",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
        
        evacuated_x = bar_width * 5
        Text(
            origin=(evacuated_x, HEIGHT - 70),
            text=f"Эвакуировано: {self.stats.evacuated} чел.",
            font=font_small,
            color=WHITE,
            should_center=False
        ).draw()
    
    def draw_history_fact(self):
        screen.blit(self.history_facts_background, (0, 0))
        
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
            text=self.current_history_fact,
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
            origin=(WIDTH//2, HEIGHT//4),
            text="БЛОКАДА ПРОРВАНА!",
            font=font_large,
            color=GOLD
        ).draw()
        
        # Расчет результатов
        survival_bonus = min(100, self.stats.health + self.stats.morale)
        food_score = min(100, self.stats.total_delivered // 20)
        evacuation_score = min(100, self.stats.evacuated * 10)
        total_score = (survival_bonus + food_score + evacuation_score) // 3
        
        # Описание результата
        result_desc = (
            f"27 января 1944 года - Ленинград полностью свободен!\n\n"
            f"Ваш вклад в победу:\n"
            f"Доставлено продовольствия: {self.stats.total_delivered} кг\n"
            f"Эвакуировано людей: {self.stats.evacuated}\n"
            f"Здоровье: {self.stats.health}% | Боевой дух: {self.stats.morale}%\n\n"
            f"Общая оценка подвига: {total_score}/100"
        )
        
        Text(
            origin=(WIDTH//2, HEIGHT//2 - 50),
            text=result_desc,
            font=font_medium,
            color=WHITE
        ).draw()
        
        Text(
            origin=(WIDTH//2, HEIGHT - 100),
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