def decimal_to_binary(num: int, width: int) -> str:

    # Validate inputs
    if not isinstance(num, int):
        raise ValueError("For signed mode, pass an integer.")
    if not isinstance(width, int) or width < 1:
        raise ValueError("You must specify a positive bit-width for signed conversion.")

    # Mask to `width` bits (handles negative wrap-around automatically)
    mask = (1 << width) - 1
    twos = num & mask

    # Convert to binary and pad with leading zeros
    return format(twos, "b").zfill(width)


def binary_to_decimal(bin_str: str, signed: bool = False) -> int:

    width = len(bin_str)
    unsigned_val = int(bin_str, 2)

    if not signed:
        return unsigned_val

    # signed two's-complement: if highest bit is 1, subtract 2**width
    if bin_str[0] == "1":
        return unsigned_val - (1 << width)
    else:
        return unsigned_val


def sign_extend(val: int, width: int, signed=True) -> int:
    if width == 0:
        return val
    return binary_to_decimal(decimal_to_binary(val, width), signed=signed)
