from renderer import common

import random

class LineSegment(object):
    def __init__(self, terminals, n_joints=30):
        # Points for all joints!
        self.joints = [None,] * n_joints

        # Which joints have been modified? These are the ones that actually need to be rendered.
        # The method get_joints() will return only those marked as 'True'
        self.joints_exist = [False,] * n_joints

        self.joints[0] = terminals[0]
        self.joints[-1] = terminals[1]
        self.joints_exist[0] = True
        self.joints_exist[-1] = True

        self.dx = terminals[1][0] - terminals[0][0]
        self.dy = terminals[1][1] - terminals[0][1]

        segment_x = self.dx / (n_joints - 1)
        segment_y = self.dy / (n_joints - 1)

        for i in range(1, len(self.joints)):
            self.joints[i] = [
                self.joints[i-1][0] + segment_x,
                self.joints[i-1][1] + segment_y,
            ]

    def rand_idx(self):
        n_joints = len(self.joints)
        options = []

        bot_q = int(n_joints / 4)
        mid_q = int(n_joints / 2)
        top_q = int(3 * n_joints / 4)

        for i in range(2, bot_q):
            options += [i,]

        for i in range(bot_q, mid_q):
            options += [i, i]

        for i in range(mid_q, top_q):
            options += [i, i, i, i]

        for i in range(top_q, n_joints - 1):
            options += [i, i]

        choice = random.choice(options)
        
        return choice
        # return random.randint(2, len(self.joints) - 1)

    def _valid_joint(self, joint_idx, point):
        # If this is the left side line
        if self.dx > 0:
            # Joints can't go to the left of the BL point
            if point[0] < self.joints[0][0]:
                return False
            
            # Joints can't dip below the BL point
            if point[1] > self.joints[0][1]:
                return False
            
            # Joints can't go right of the TC point
            if point[0] > self.joints[-1][0]:
                return False

        # If this is the right side line
        if self.dx < 0:
            # Joints can't go to the right of the BR point
            if point[0] > self.joints[0][0]:
                return False
            
            # Joints can't dip below the BR point
            if point[1] > self.joints[0][1]:
                return False
            
            # Joints can't go left of the TC point
            if point[0] < self.joints[-1][0]:
                return False

        return True

    def add_joint(self, joint_idx, max_dev, force=False):
        if self.joints_exist[joint_idx]:
            return

        x_delta = random.random() * max_dev
        y_delta = random.random() * max_dev

        revised = [None, None]
        if random.random() < 0.5:
            revised[0] = self.joints[joint_idx][0] + x_delta
        else:
            revised[0] = self.joints[joint_idx][0] - x_delta
        
        if random.random() < 0.5:
            revised[1] = self.joints[joint_idx][1] + y_delta
        else:
            revised[1] = self.joints[joint_idx][1] - y_delta

        if force or self._valid_joint(joint_idx, revised):
            self.joints[joint_idx] = revised

            # Only allow adding a joint to this idx one time, otherwise we can get major
            # unintended offsets in certain cases
            self.joints_exist[joint_idx] = True
        else:
            self.add_joint(joint_idx, max_dev)
    
    def get_joints(self):
        points = []

        for i, point in enumerate(self.joints):
            if self.joints_exist[i]:
                points.append(point)
   
        return points

def _draw_diagonals(ctx, bl_pt, tc_pt, region):
    n_diagonals = 14

    dx = 2 * (tc_pt[0] - bl_pt[0]) / n_diagonals
    dy = 2 * (tc_pt[1] - bl_pt[1]) / n_diagonals

    ctx.move_to(*region[0])

    # Create clipping region
    for pt in region[1:]:
        ctx.line_to(*pt)

    ctx.close_path()
    ctx.clip()

    # Draw diagonals inside of clipping region
    for i in range(1, n_diagonals):
        left_pt = (bl_pt[0], bl_pt[1] + (i * dy))
        right_pt = (bl_pt[0] + (i * dx), bl_pt[1])

        ctx.move_to(*left_pt)
        ctx.line_to(*right_pt)

    ctx.stroke()

def _shade_region(ctx, region, color):
    ctx.move_to(*region[0])

    for pt in region:
        ctx.line_to(*pt)
    
    ctx.set_source_rgb(*color)
    ctx.fill()

def _draw_line(ctx, line, width):
    ctx.move_to(*line[0])

    for i in range(1, len(line)):
        ctx.line_to(*line[i])
    
    ctx.set_line_width(width)
    ctx.stroke()

def draw_mountain(ctx, pos, cell_ctx):
    '''

    ctx         -> cairo drawing context
    pos         -> bottom center point
    cell_ctx    -> dict with params for rendering (colors, etc)
    '''

    fill_color = cell_ctx['fill_color']

    width = cell_ctx['width']
    height = width / 1.36 # ratio (300:220 during design phase)

    outline_width = width / 20
    ridgeline_max_noise = width / 300
    ridgeline_dx = width * (random.random() * ridgeline_max_noise)

    # Basic form
    bl_pt = (pos[0] - (width / 2), pos[1])
    tc_pt = (pos[0], pos[1] - height)
    bc_pt = (pos[0] - ridgeline_dx, pos[1]) # add in a random shift left
    br_pt = (pos[0] + (width / 2), pos[1])

    left = LineSegment( (bl_pt, tc_pt) )
    right = LineSegment( (br_pt, tc_pt) )

    left.add_joint(left.rand_idx(), width * 0.10)
    if random.random() < 0.5:
        left.add_joint(left.rand_idx(), width * 0.10)

    right.add_joint(right.rand_idx(), width * 0.10)
    if random.random() < 0.5:
        right.add_joint(right.rand_idx(), width * 0.10)

    ctx.set_source_rgb(0.1, 0.1, 0.1)

    _draw_line(ctx, left.get_joints(), outline_width)
    _draw_line(ctx, right.get_joints(), outline_width)

    # Calculate (but don't render) ridgeline
    ridge = LineSegment( (tc_pt, bc_pt) )
    ridge.add_joint(ridge.rand_idx(), width * 0.05, force=True)

    # Light side
    light_region = ridge.get_joints() + right.get_joints() + [ridge.get_joints()[0],]
    _shade_region(ctx, light_region, fill_color)

    # Shadow side, including diagonals
    dark_region = left.get_joints() + ridge.get_joints() + [left.get_joints()[0],]
    _shade_region(ctx, dark_region, common.add_color(fill_color, -0.1))

    ctx.set_source_rgb(0.5, 0.5, 0.5)
    ctx.set_line_width(outline_width * 0.6)
    _draw_diagonals(ctx, bl_pt, tc_pt, dark_region)

    # Render ridgeline
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    _draw_line(ctx, ridge.get_joints(), outline_width * 0.8)