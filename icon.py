from random import random
import cairo
from renderer.mountain import draw_mountain

dims = (400, 400)

def run():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *dims)
    ctx = cairo.Context(surface)

    fill_color = (0.95, 0.95, 0.95)

    # Background fill
    ctx.rectangle(0, 0, *dims)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()

    # Mode 1: zoom
    # draw_mountain(ctx, (200, 300), {
    #     'fill_color': fill_color,
    #     'width': 300,
    # })

    # Mode 2: zoom
    row_count = 4
    col_count = 8
    padding = dims[0] * 0.2
    x_delta = (dims[0] - padding) / col_count
    y_delta = (dims[1] - padding) / row_count

    mountain_width = 40

    for y in range(row_count):
        y_pos = (padding / 2) + (y_delta * y) + mountain_width

        for x in range(col_count):
            x_pos = (padding / 2) + (x_delta * x) + (5 * x)

            ctx.rectangle(
                x_pos - (mountain_width / 2), 
                y_pos - mountain_width, 
                mountain_width, 
                mountain_width,
            )
            ctx.set_source_rgb(0.4, 0.4, 0.4)
            ctx.fill_preserve()

            ctx.set_source_rgb(0, 0, 0)
            ctx.set_line_width(2)
            ctx.stroke()

            ctx.save()
            draw_mountain(ctx, (x_pos, y_pos), {
                'fill_color': fill_color,
                'width': 40,
            })
            ctx.restore()

    surface.write_to_png('icon.png')

run()