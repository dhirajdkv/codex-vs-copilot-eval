#!/usr/bin/env python3

def trap(heights):
    """
    Problem: Trapping Rain Water
    Given n non-negative integers representing an elevation map where the width of each bar is 1,
    compute how much water it can trap after raining.
    """
    if not heights:
        return 0
    
    left, right = 0, len(heights) - 1  # Two pointers: left and right
    max_left, max_right = heights[left], heights[right]  # Initial maximum heights
    trap_water = 0  # Accumulated water
    
    while left < right:
        max_left = max(max_left, heights[left])
        max_right = max(max_right, heights[right])
        if max_left <= max_right:
            trap_water += max_left - heights[left]
            left += 1
        else:
            trap_water += max_right - heights[right]
            right -= 1
    
    return trap_water

# Test cases
def test_trap():
    assert trap([0,1,0,2,1,0,1,3,2,1,2,1]) == 6
    assert trap([4,2,0,3,2,5]) == 9 