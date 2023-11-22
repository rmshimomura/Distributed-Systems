response = b'M:315,174,539,393'
points = response[2:].decode().split(',')
p1 = (int(points[0]), int(points[1]))
p2 = (int(points[2]), int(points[3]))

if 'C' in response.decode():
    # Create the line
    print(f"Creating line on coords:")    
    print(f"Start: {p1}")
    print(f"End: {p2}")
elif 'M' in response.decode():
    # Move the line
    print(f"Moving line on coords {response[2:].decode()}")
    print(f"Start: {p1}")
    print(f"End: {p2}")

print(points)