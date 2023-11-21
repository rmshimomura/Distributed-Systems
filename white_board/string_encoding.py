list_t =  [[(1399, 611), (1284, 527)], [(500, 161), (903, 348)], [(1088, 113), (938, 549)], [(1351, 258), (1470, 457)]]

# Transform the list into a string
result_string = ';'.join(['|'.join([f"{x},{y}" for x, y in inner_tuple]) for inner_tuple in list_t])

print(result_string)

# for start_point, a in [wow.split('|') for wow in result_string.split(';')]:
#     print(start_point.split(','), a.split(',') )