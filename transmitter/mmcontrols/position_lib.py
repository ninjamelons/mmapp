# x_pos, y_pos = current coordinate position
# noPoints = number of points in grid to be scanned
def GetNextPositionSpiral(x_pos, y_pos, noPoints):
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
# x_pos/y_pos - refer above
# height/width = dimensions of rectangle to scan
def GetNextPositionRect(x_pos, y_pos, height, width):
    xypoint_pos = [0, 0, height, width, False]
    # If current x position = width, then go to next row
    if(x_pos == width):
        xypoint_pos[0] = 0
    else:
        xypoint_pos[0] = x_pos + 1

    # If current y position = height, then go to next column
    if(y_pos == height):
        xypoint_pos[1] = 0
    else:
        xypoint_pos[1] = y_pos + 1
    
    # If next x position = width, and current y position = height,
    # then this is final point
    if(x_pos + 1 == width and y_pos == height):
        xypoint_pos[4] = True
    
    return xypoint_pos

# x,y = Current position
# x_pos,y_pos = Next position
def GetDxDy(curr_x, curr_y, next_x, next_y):
    dx,dy = 0, 0
    dx = next_x - curr_x
    dy = next_y - curr_y
    return [dx,dy]