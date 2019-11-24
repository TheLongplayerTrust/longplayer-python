import sys

ansi_clear_lines = lambda count: "\n" * count
ansi_move_left = lambda: "\u001b[1000D"
ansi_move_up = lambda count: "\u001b[%dA" % count
ansi_dash = lambda: "\u2014"
ansi_block_light = lambda: "\u2591"
ansi_block = lambda: "\u2588"


def ansi_bar(width, bar_min, bar_cursor, bar_max):
    rv = "["
    rv += ansi_dash() * bar_min
    rv += ansi_block_light() * (bar_cursor - bar_min)
    rv += ansi_block()
    rv += ansi_block_light() * (bar_max - bar_cursor - 1)
    rv += ansi_dash() * (width - bar_max)
    rv += "]"
    return rv


class BarRenderer(object):
    def __init__(self, width, bar_count):
        self.width = width
        self.bar_count = bar_count
        sys.stdout.write(ansi_clear_lines(self.bar_count))

    def clear(self):
        sys.stdout.write(ansi_move_up(self.bar_count))

    def draw_bar(self, offset, position, width):
        sys.stdout.write(ansi_move_left())

        segment_start = offset
        segment_cursor = min(offset + position, self.width)
        segment_end = min(offset + width, self.width)
        sys.stdout.write(ansi_bar(self.width, segment_start, segment_cursor, segment_end) + "\n")
