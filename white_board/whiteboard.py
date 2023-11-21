import pygame, sys

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

class Whiteboard:

    def __init__(self, width, height, name):

        self.start_window(width, height, name)
        self.exit_flag = False
        self.first_start = True
        self.lines = []

    def start_window(self, width, height, name):
            
        self.width = width
        self.height = height
        self.name = name

        self.dragging_line_start = False
        self.dragging_line_end = False
        self.line_creation = False
        self.start_point_motion = None
        self.end_point_motion = None
    
        self.window = None

    def initialize_pygame(self, name):
        self.pygame_instance = pygame
        self.pygame_instance.init()
        self.window = self.pygame_instance.display.set_mode((self.width, self.height))
        self.pygame_instance.display.set_caption(f"Whiteboard {name}")
        self.window.fill(WHITE)
        self.exit_flag = False

    def add_line(self, line):

        self.lines.append(line)

    def render(self):

        self.initialize_pygame(self.name)

        while not self.exit_flag:

            self.render_lines()

            self.pygame_instance.display.flip()

            # Control the frame rate
            self.pygame_instance.time.Clock().tick(60)

            self.handle_events()
            
    def render_lines(self):

        if len(self.lines):

            for line, (start, end) in enumerate(self.lines):
                self.pygame_instance.draw.line(self.window, BLACK, start, end, 2)
                self.pygame_instance.draw.circle(self.window, RED, start, 5)
                self.pygame_instance.draw.circle(self.window, RED, end, 5)

            if self.start_point_motion and self.end_point_motion:
                self.pygame_instance.draw.line(self.window, BLACK, self.start_point_motion, self.end_point_motion, 2)
                self.pygame_instance.draw.circle(self.window, RED, self.start_point_motion, 5)
                self.pygame_instance.draw.circle(self.window, RED, self.end_point_motion, 5)

    def handle_events(self):

        for event in self.pygame_instance.event.get():

            if event.type == self.pygame_instance.QUIT:
                self.pygame_instance.quit()
                self.exit_flag = True

            elif event.type == self.pygame_instance.MOUSEBUTTONDOWN:

                if event.button == self.pygame_instance.BUTTON_LEFT:
                    # Create a line if the left button is pressed
                    
                    if self.line_creation:
                        self.lines.append([self.line_start_point, event.pos])
                        self.line_creation = False
                    else:
                        self.line_start_point = event.pos
                        self.line_creation = True

                elif event.button == self.pygame_instance.BUTTON_RIGHT:
                    # Move a line if the right button is pressed

                    for i, (p1, p2) in enumerate(self.lines):
                        self.line_start = self.pygame_instance.Rect(p1[0] - 5, p1[1] - 5, 10, 10)
                        self.line_end = self.pygame_instance.Rect(p2[0] - 5, p2[1] - 5, 10, 10)

                        # Check hitboxes

                        if self.line_start.collidepoint(event.pos):
                            self.start_point_motion, self.end_point_motion = p1, p2
                            self.dragging_line_start = True
                            self.lines.pop(i)
                            break

                        elif self.line_end.collidepoint(event.pos):
                            self.start_point_motion, self.end_point_motion = p1, p2
                            self.dragging_line_end = True
                            self.lines.pop(i)
                            break


            elif event.type == self.pygame_instance.MOUSEMOTION:

                # Update the coordinates when dragging
                if self.dragging_line_start:
                    self.start_point_motion = event.pos
                elif self.dragging_line_end:
                    self.end_point_motion = event.pos

            elif event.type == self.pygame_instance.MOUSEBUTTONUP:

                # Stop dragging when the mouse button is released

                if event.button == self.pygame_instance.BUTTON_RIGHT:

                    if self.dragging_line_start or self.dragging_line_end:

                        self.lines.insert(0, [self.start_point_motion, self.end_point_motion])
                        self.dragging_line_start = False
                        self.dragging_line_end = False
                        self.start_point_motion = None
                        self.end_point_motion = None
