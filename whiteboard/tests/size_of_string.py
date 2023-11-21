import sys

your_string = "1399|611,1284|527;500|161,903|348;1088|113,938|549;1351|258,1470|457"

size_in_bytes = sys.getsizeof(your_string)
print(f"The size of the string in bytes is: {size_in_bytes}")
