import pygame
import random
import dataclasses
from datetime import datetime, timedelta

# Исторические даты блокады
BLOCKADE_START = datetime(1941, 9, 8)
BLOCKADE_END = datetime(1944, 1, 27)

# Ограничение параметров
MAX_FOOD = 250
MAX_HEALTH = 100
MAX_MORALE = 100

import os

def load_image(file_path, convert_alpha=False, scale=None):
    """
    Загружает картинку.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")
    
    try:
        if convert_alpha:
            surface = pygame.image.load(file_path).convert_alpha()
        else:
            surface = pygame.image.load(file_path).convert()
            
        if scale is not None:
            surface = pygame.transform.scale(surface, scale)
            
        return surface
        
    except pygame.error as e:
        raise pygame.error(f"Failed to load image {file_path}: {e}")

def create_image(base_color: pygame.Color, width: int, height: int):
    """Создает изображение с текстурой"""
    surface = pygame.Surface((width, height))
    surface.fill(base_color)
    
    # Добавляем текстуру
    for _ in range(2000):
        x, y = random.randint(0, width), random.randint(0, height)
        brightness = random.randint(-30, 30)
        color = (
            max(0, min(255, base_color[0] + brightness)),
            max(0, min(255, base_color[1] + brightness)),
            max(0, min(255, base_color[2] + brightness))
        )
        pygame.draw.circle(surface, color, (x, y), random.randint(1, 5))
    
    return surface

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

def get_scenes(width: int, height: int) -> list[Scene]:
    return [
        Scene(
                title="Начало блокады",
                text="Сентябрь 1941 года. Немецкие войска замкнули кольцо вокруг Ленинграда.\n"
                     "Вы - водитель грузовика, которому поручено проложить путь через Ладожское озеро.\n"
                     "Какой груз взять для первого рейса?",
                background=load_image("pic1.png", scale=(width, height)),
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
                background=create_image((70, 90, 80), width, height),
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
                background=load_image("pic2.png", scale=(width, height)),
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
                background=create_image((60, 60, 70), width, height),
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
                background=load_image("pic3.png", scale=(width, height)),
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
                                modifier=PlayerStatsModifier(-100, -30, -20, evacuated=5)
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
                background=create_image((70, 100, 120), width, height),
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
                background=load_image("pic4.png", scale=(width, height)),
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
                background=create_image((40, 60, 80), width, height),
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
                background=create_image((90, 70, 80), width, height),
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
                background=create_image((100, 100, 120), width, height),
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