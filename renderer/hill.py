import cairo, random

from renderer import common

width = 0.012 # 8:3 width/height ratio
height = width * (1 / 2)

def draw_hill(ctx, pos, cell_ctx):
    width = 0.012 + random.random() * 0.01
    height = width * 0.5

    fill_color = cell_ctx['fill_color']

    # Main hill
    a = ( pos[0] - (width / 2), pos[1] )
    b = ( a[0] + (width / 3), a[1] - height )
    c = ( a[0] + (2 * width / 3), a[1] - height )
    d = ( pos[0] + (width / 2), pos[1] )

    # Hill shadow
    ctx.move_to(a[0] - 0.002, a[1] - 0.001)
    ctx.curve_to(
        b[0] - 0.002, b[1] - 0.001,
        c[0] - 0.002, c[1] - 0.001,
        d[0] - 0.002, d[1] - 0.001,
    )
    ctx.line_to(*a)     # fill shadow between hill and shadow
    ctx.line_to(
        a[0] - 0.002, 
        a[1] - 0.001,
    )

    ctx.set_source_rgba(*common.add_color(fill_color, 0.3), 0.6)
    ctx.fill()

    # Hill foreground
    ctx.move_to(*a)
    ctx.curve_to(*b, *c, *d)

    ctx.set_source_rgba(*fill_color)
    ctx.fill_preserve()

    ctx.set_source_rgb(0, 0, 0)
    ctx.set_line_width(0.001)
    ctx.stroke()


    # Highlight on right-hand side
    a_x = (
        0.001+ a[0] + (width / 2), 
        0.0005 + (a[1] + b[1]) / 2,
    )

    d_x = (
        d[0] - 0.002,
        d[1] - 0.001
    )

    ctx.move_to(*a_x)
    ctx.curve_to(
        a_x[0] + 0.002,
        a_x[1] + 0.001, 
        d_x[0] - 0.002, 
        d_x[1] - 0.002, 
        *d_x,
    )

    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(0.0013)
    ctx.set_source_rgba(0.6, 0.6, 0.6, 0.9)
    ctx.stroke()