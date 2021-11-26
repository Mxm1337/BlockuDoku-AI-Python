# TODO: optional: add more state

import pygame as pg
from GridCell import *
from Shape import *
import random
import numpy as np
import time

MOVEMENT_PUNISHMENT = -1
INVALID_MOVEMENT_PUNISHMENT = -10
INVALID_PLACEMENT_PUNISHMENT = -20
LOSE_PUNISHMENT = 0


class Blockudoku:

    def __init__(self, seed):
        random.seed(seed)
        self.window_size = pg.Vector2(450, 700)
        self.board_loc = pg.Vector2(1, 90)
        self.board_size = pg.Vector2(self.window_size.x - 2, self.window_size.x)
        self.cell_size = self.window_size.x // 9
        self.grid = []
        self.score = 0
        self.cleared_recently = False
        self.lost = False
        self.state = np.zeros((2, 9, 9))
        # possible states:
        # * invalid cells
        # * blocks that will be cleared if shape is placed
        # * cells' boarders

        for r in range(9):
            self.grid.append([])
            for c in range(9):
                self.grid[r].append(GridCell(r, c))

        self.current_shape = Shape()

    def restart(self):
        self.score = 0
        self.cleared_recently = False
        self.lost = False
        self.state = np.zeros((2, 9, 9))
        self.current_shape = Shape()
        for row in range(9):
            for col in range(9):
                self.grid[row][col].empty = True

    def drawGame(self, screen):
        running = True

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    self.restart()
                if event.key == pg.K_SPACE:
                    self.step(0)
                if event.key == pg.K_RIGHT:
                    self.step(1)
                if event.key == pg.K_DOWN:
                    self.step(2)
                if event.key == pg.K_LEFT:
                    self.step(3)
                if event.key == pg.K_UP:
                    self.step(4)
                self.drawGame(screen)

        screen.fill((255, 255, 255))

        self._drawCells(screen, self.grid, self.cell_size, self.board_loc)
        self.current_shape.draw(screen, self.board_loc, self.cell_size, self.grid)
        self._drawBorders(screen, self.cell_size, self.board_loc, self.board_size)
        self._displayScore(screen)

        pg.display.flip()

        return running

    def step(self, action):
        if action == 0:  # place
            valid = self.current_shape.place(self.grid)
            if valid:
                reward = self._blockPlaced()
            else:
                reward = INVALID_PLACEMENT_PUNISHMENT

        else:
            if action == 1:
                valid = self.current_shape.moveRight()
            elif action == 2:
                valid = self.current_shape.moveDown()
            elif action == 3:
                valid = self.current_shape.moveLeft()
            else:
                valid = self.current_shape.moveUp()

            if valid:
                reward = MOVEMENT_PUNISHMENT
            else:
                reward = INVALID_MOVEMENT_PUNISHMENT

        self._calculateState()
        return self.state, reward, self.lost

    def _calculateState(self):
        # layer 1: filled cells
        for row in range(9):
            for col in range(9):
                if self.grid[row][col].empty:
                    self.state[0][row][col] = 0
                else:
                    self.state[0][row][col] = 1

        # layer 2: current shape
        self.state[1] = np.zeros(self.state[1].shape)
        for block in self.current_shape.blocks:
            self.state[1][self.current_shape.row + block[0]][self.current_shape.col + block[1]] = 1

    def _scoreBoard(self):
        cleared_blocks = []

        # check for vertical lines
        for row in range(9):
            cleared = True
            for col in range(9):
                if self.grid[row][col].empty:
                    cleared = False
                    break

            if cleared:
                cleared_blocks += self.grid[row]

        # check for horizontal lines
        for col in range(9):
            cleared = True
            for row in range(9):
                if self.grid[row][col].empty:
                    cleared = False
                    break

            if cleared:
                cleared_blocks += [grid_row[col] for grid_row in self.grid]

        # check for cleared squares
        for square_row in range(0, 9, 3):
            for square_col in range(0, 9, 3):
                cleared = True
                for row in range(3):
                    for col in range(3):
                        if self.grid[square_row+row][square_col+col].empty:
                            cleared = False
                            break

                if cleared:

                    for row in range(3):
                        for col in range(3):
                            cleared_blocks.append(self.grid[square_row+row][square_col+col])

        # give score
        reward = 0
        if len(cleared_blocks) > 0:
            if len(cleared_blocks) <= 18:
                reward += len(cleared_blocks) * 2
            else:
                reward += len(cleared_blocks) * 4

            for cleared_block in cleared_blocks:
                cleared_block.empty = True

        return reward

    def _blockPlaced(self):
        reward = 0
        reward += self._scoreBoard()
        if reward > 0:
            if self.cleared_recently:
                reward += 9
            self.cleared_recently = True
        else:
            self.cleared_recently = False

        reward += self.current_shape.remainingBlocks(self.grid)
        self.score += reward

        self.current_shape = Shape()
        if not self.current_shape.validSpaceExists(self.grid):
            self.lost = True
            reward -= LOSE_PUNISHMENT

        return reward

    def _displayScore(self, screen):
        font = pg.font.SysFont(None, 44)
        if self.lost:
            color = (255, 0, 0)
        else:
            color = (0, 0, 0)
        img = font.render('Score: ' + str(self.score), True, color)
        screen.blit(img, (self.window_size.x / 2 - 60, 37))

    def _drawCells(self, screen, grid, cell_size, board_loc):
        for r in range(9):
            for c in range(9):
                grid[r][c].draw(screen, board_loc, cell_size)

    def _drawBorders(self, screen, cell_size, board_loc, board_size):
        color = (0, 0, 0)

        rect = pg.Rect(board_loc.x + cell_size * 3, board_loc.y, cell_size * 3, board_size.y)
        pg.draw.rect(screen, color, rect, 2)
        rect = pg.Rect(board_loc.x, board_loc.y + cell_size * 3, board_size.x, cell_size * 3)
        pg.draw.rect(screen, color, rect, 2)

        rect = pg.Rect(board_loc.x, board_loc.y, board_size.x, board_size.y)
        pg.draw.rect(screen, color, rect, 3)


game = Blockudoku(69)

pg.init()

screen = pg.display.set_mode([game.window_size.x, game.window_size.y])

running = True
while running:
    running = game.drawGame(screen)

pg.quit()
