# x_pos, y_pos = current coordinate position
# noPoints = number of points in grid to be scanned
def GetNextPosition(x_pos, y_pos, noPoints):
    dx, segment_length = 1, 1
    dy, x, y, segment_passed = 0, 0, 0, 0
    final = False
    for i in range(0, noPoints - 1):
        if i == (noPoints - 2):
            final = True
        if x_pos == x and y_pos == y:
            xypoint_pos = [x+dx, y+dy, i+1, final]
            return xypoint_pos
        x += dx
        y += dy
        segment_passed += 1
        if segment_passed == segment_length:
            segment_passed = 0
            #Clockwise rotation
            buffer = dy
            dy = -dx
            dx = buffer
            if dy == 0:
                segment_length += 1
# x,y = Current position
# x_pos,y_pos = Next position
def GetDxDy(curr_x, curr_y, next_x, next_y):
    dx,dy = 0, 0
    dx = next_x - curr_x
    dy = next_y - curr_y
    return [dx,dy]