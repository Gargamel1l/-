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

def get_scenes(width: int, height: int) -> list[Scene]:
    return [
        Scene(
            text=f"День 1. {BLOCKADE_START.strftime('%d.%m.%Y')}\nВы загружаете грузовик на базе. Сколько продовольствия взять?",
            background=create_image((80, 80, 100), width, height),  # grey
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
            background=create_image((70, 90, 80), width, height),  # cold
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
            text=f"День 2. {(BLOCKADE_START + timedelta(days=1)).strftime('%d.%m.%Y')}\nВ небе появляются немецкие самолёты!",
            background=create_image((90, 60, 70), width, height),  # red
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
            text=f"День 3. {(BLOCKADE_START + timedelta(days=2)).strftime('%d.%m.%Y')}\nВы встретили колонну грузовиков. Командир предлагает объединиться.",
            background=create_image((60, 80, 90), width, height),  # unknown?
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
            text=f"День 4. {(BLOCKADE_START + timedelta(days=3)).strftime('%d.%m.%Y')}\nНачалась сильная метель! Видимость практически нулевая.",
            background=create_image((60, 80, 90), width, height),  # blue, snow storm
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
            text=f"День 5. {(BLOCKADE_START + timedelta(days=4)).strftime('%d.%m.%Y')}\nВы прибыли в Ленинград. Голодные жители смотрят на ваш грузовик.",
            background=create_image((90, 70, 80), width, height),  # warm, city
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