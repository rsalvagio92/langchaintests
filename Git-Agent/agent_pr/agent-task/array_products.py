from typing import List

def calculate_products(nums: List[int] ) -> List[int]:
    """"
    Calculate the product of all elements in a list except the one at each position.


    Args:
    nums (List[int]): A list of integers.

    Returns:
    List[int]: A new list where each element at index i is the product of
    all elements in the original list except the one at index i.

    Examples:
    >>> calculate_products([1, 2, 3, 4])
    [24, 12, 8, 6]

    >>> calculate_products([1, 0, 3, 4])
    [0, 0, 0, 0]

    >>> calculate_products([])
    []

    >>> calculate_products([5])
    [1]
    """
    if not nums:
        return []

    products = [1] * len(nums)
    before_product = 1

    # Calculate product before each index
    for i in range(len(nums)):
    products [i] *= before_product
    before_product *= nums [i]