import pygame
from pygame import mixer
import dataclasses
from utility import *

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

STATE_MENU = 0
STATE_CHOICE = 1
STATE_RESULT = 2
STATE_HISTORY = 3
STATE_GAME_OVER = 4
STATE_VICTORY = 5

# Ограничение частоты кадров
MAX_FPS = 30

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

        self.init_state_menu()
        self.init_state_result()
        self.init_state_choice()
        self.init_state_history()
        self.init_state_victory()
        self.init_state_game_over()

        self.state = STATE_MENU
        self.scene_index = 0
        self.current_scene = None
        self.stats: PlayerStats
        
        self.load_story()
    
    def init_state_menu(self):
        self.menu_background = create_image((50, 70, 90), WIDTH, HEIGHT)  # Темно-синий
        self.menu_title = Text(
            origin=(WIDTH//2, HEIGHT//4),
            font=font_large,
            text="ДОРОГА ЖИЗНИ",
            color=GOLD
        )
        self.menu_subtile = Text(
            origin=(WIDTH//2, HEIGHT//4 + 50),
            font=font_medium,
            text="Блокада Ленинграда 1941-1944",
            color=WHITE
        )
        self.menu_button_begin = Button(
            rect=pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 50),
            fill_color=DARK_RED,
            outline_width=2,
            outline_color=BLACK
        )
        self.menu_button_begin_text = Text(
            origin=(WIDTH//2, HEIGHT//2),
            width=300,
            font=font_medium,
            text="НАЧАТЬ ИГРУ",
            color=WHITE
        )
    
    def init_state_result(self):
        self.result_text = Text(
            origin=(50, 30),
            width=WIDTH - 100,
            font=font_small,
            text="",
            color=WHITE,
            should_center=False
        )
        
        self.result_button_next = Button(
            rect=pygame.Rect(WIDTH//2 - 200, HEIGHT - 200, 400, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        )
        self.result_button_next_text = Text(
            origin=(WIDTH//2, HEIGHT - 200),
            font=font_medium,
            text="ПРОДОЛЖИТЬ",
            color=WHITE
        )
    
    def init_state_choice(self):
        self.buttons: list[tuple[Button, Text]] = []
        self.choices = []
    
    def init_state_history(self):
        self.history_facts_background = create_image((70, 70, 90), WIDTH, HEIGHT)

        self.history_facts = [
            "Блокада Ленинграда длилась с 8 сентября 1941 года по 27 января 1944 года (872 дня). Это самая продолжительная и разрушительная блокада в истории человечества.",
            "Дорога жизни - ледовая трасса через Ладожское озеро. Зимой 1941-1942 по ней доставляли 2000 тонн грузов ежедневно. Каждый рейс был смертельно опасен.",
            "Норма хлеба для рабочих в ноябре 1941 года составляла 250 грамм в день, для остальных - 125 грамм. Люди умирали от голода прямо на улицах."
        ]
        self.history_facts_shown = []

        self.history_title = Text(
            origin=(WIDTH//2, 50),
            text="ИСТОРИЧЕСКАЯ СПРАВКА",
            font=font_large,
            color=GOLD
        )

        self.history_fact_text = Text(
            origin=(50, 150),
            width=WIDTH - 100,
            text="",
            font=font_historical,
            color=WHITE,
            should_center=False
        )

        self.history_fact_button_next = Button(
            rect=pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 50),
            fill_color=BLUE,
            outline_width=2,
            outline_color=BLACK
        )
        self.history_fact_button_next_text = Text(
            origin=(WIDTH//2, HEIGHT - 100),
            text="ПРОДОЛЖИТЬ",
            font=font_medium,
            color=WHITE,
            should_center=True
        )

    def init_state_victory(self):
        self.victory_title = Text(
            origin=(WIDTH//2, HEIGHT//3),
            text="ПОБЕДА!",
            font=font_large,
            color=GOLD
        )
        self.vicoty_text = Text(
            origin=(WIDTH//2, HEIGHT//2),
            text=f"Вы продержались до конца!\n" +
                 "Ваши усилия помогли спасти жизни ленинградцев.\n" +
                 "Нажмите R для перезапуска",
            font=font_medium,
            color=WHITE
        )
    
    def init_state_game_over(self):
        self.game_over_reason = ""

        self.game_over_title = Text(
            origin=(WIDTH//2, HEIGHT//3),
            text="ИГРА ОКОНЧЕНА",
            font=font_large,
            color=RED
        )
        self.game_over_subtile = Text(
            origin=(WIDTH//2, HEIGHT//2),
            font=font_medium,
            color=WHITE
        )
    
    def load_story(self):
        self.story_scenes = get_scenes(WIDTH, HEIGHT)

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
                elif event.key == pygame.K_r and self.state == STATE_GAME_OVER:
                    self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_click(event.pos)

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_CHOICE:
            self.draw_game()
        elif self.state == STATE_RESULT:
            self.draw_result()
        elif self.state == STATE_HISTORY:
            self.draw_history_fact()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_VICTORY:
            self.draw_victory()
        
        pygame.display.flip()
        self.fps_clock.tick(MAX_FPS)
    
    def handle_click(self, pos):
        if self.state == STATE_MENU:
            if self.menu_button_begin.contains_point(pos):
                self.start_game()
        
        elif self.state == STATE_CHOICE:
            for i in range(len(self.buttons)):
                (button, _) = self.buttons[i]
                if button.contains_point(pos):
                    self.process_choice(i)
                    break
        
        elif self.state == STATE_HISTORY:
            if self.history_fact_button_next.contains_point(pos):
                self.next_scene()
        
        elif self.state == STATE_RESULT:
            if self.result_button_next.contains_point(pos):
                if self.check_game_failed():
                    self.begin_state_game_over()
                else:
                    self.begin_state_history()
    
    def start_game(self):
        self.stats = PlayerStats(0, 100, 100)
        self.scene_index = 0
        self.history_facts_shown = []
        self.begin_state_choices()
    
    def begin_result_with_text(self, text: str):
        self.result_text.text = text
        self.state = STATE_RESULT
    
    def begin_state_choices(self):
        self.state = STATE_CHOICE
        self.current_scene = self.story_scenes[self.scene_index]
        self.choices = self.current_scene.choices
        self.buttons = []
        
        for i, choice in enumerate(self.choices):
            button = Button(
                rect=pygame.Rect(WIDTH//4, HEIGHT//2 + i * 90, WIDTH//2, 80),
                fill_color=DARK_RED if i % 2 == 0 else BLUE,
                outline_width=2,
                outline_color=BLACK
            )
            text = Text(
                origin=(WIDTH//2, HEIGHT//2 + i * 90),
                width=WIDTH//2,
                font=font_small,
                text=choice.text,
                color=WHITE
            )
            self.buttons.append((button, text))
    
    def begin_victory(self):
        self.state = STATE_VICTORY
    
    def begin_state_game_over(self):
        self.game_over_subtile.text = self.game_over_reason + '\n' + "Нажмите R для перезапуска"
        self.state = STATE_GAME_OVER
    
    # def show_history_fact(self):
    def begin_state_history(self):
        available_facts = [f for f in self.history_facts if f not in self.history_facts_shown]
        if not available_facts:
            available_facts = [f for f in self.history_facts]
            self.history_facts_shown = []
        
        current_history_fact = random.choice(available_facts)
        self.history_facts_shown.append(current_history_fact)
        self.history_fact_text.text = current_history_fact
        self.state = STATE_HISTORY
    
    def process_choice(self, choice_index):
        text = self.choices[choice_index].consequence.apply_consequences(self.stats)
        self.begin_result_with_text(text)
    
    def next_scene(self):
        self.scene_index += 1
        
        if self.scene_index >= len(self.story_scenes):
            self.begin_victory()
        else:
            self.begin_state_choices()
    
    def check_game_failed(self) -> bool:
        if self.stats.food <= 0:
            self.game_over_reason = "Весь груз еды был утерян..."
            return True
        elif self.stats.health <= 0:
            self.game_over_reason = "Ваше здоровье ухудшилось слишком сильно..."
            return True
        elif self.stats.morale <= 0:
            self.game_over_reason = "Вы потеряли волю к продолжению..."
            return True
        # elif self.ice_stability <= 0:
        #     self.begin_state_game_over("Лёд стал слишком опасным для движения...")
        
        return False
    
    def draw_menu(self):
        screen.blit(self.menu_background, (0, 0))
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        self.menu_title.draw()
        self.menu_subtile.draw()
        self.menu_button_begin.draw()
        self.menu_button_begin_text.draw()
    
    def draw_game(self):
        if self.current_scene.background:
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
        
        for button, text in self.buttons:
            button.draw()
            text.draw()
    
    def draw_result(self):
        if self.current_scene and self.current_scene.background:
            screen.blit(self.current_scene.background, (0, 0))
        else:
            screen.fill(GRAY)
        
        text_bg = pygame.Surface((WIDTH - 40, HEIGHT//3), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 180))
        screen.blit(text_bg, (20, 20))

        self.draw_status_bar()
        self.result_text.draw()
        self.result_button_next.draw()
        self.result_button_next_text.draw()
    
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
        
        self.history_title.draw()
        self.history_fact_text.draw()
        self.history_fact_button_next.draw()
        self.history_fact_button_next_text.draw()
    
    def draw_game_over(self):
        screen.fill(BLACK)
        
        self.game_over_title.draw()
        self.game_over_subtile.draw()
    
    def draw_victory(self):
        screen.fill(BLUE)
        
        self.victory_title.draw()
        self.vicoty_text.draw()
    
    def reset_game(self):
        self.__init__()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()