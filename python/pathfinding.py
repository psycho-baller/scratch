def collect_letters(grid):
    # Dimensions of the grid
    rows, cols = len(grid), len(grid[0])

    # Directions: right, down, left, up
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # Start position
    x, y = 0, 0
    visited = set()
    letters = []

    def dfs(x, y):
        # Skip already visited cells
        if (x, y) in visited:
            print(f"Skipping ({x}, {y}) as it is already visited")  # Debug log
            return
        visited.add((x, y))
        print(f"Visited: {visited}")  # Debug log

        # Collect letters
        if grid[x][y].isalpha():
            letters.append(grid[x][y])
            print(f"Collected letter: {grid[x][y]}")  # Debug log

        # Check neighbors in 4 directions
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited:
                # Continue if next cell is '*' or a letter
                if grid[nx][ny] == "*" or grid[nx][ny].isalpha():
                    print(f"Recursing into ({nx}, {ny})")  # Debug log
                    dfs(nx, ny)

    # Start the recursive DFS
    dfs(x, y)

    # Return the collected letters as a string
    print(f"Final collected letters: {''.join(letters)}")  # Debug log
    return "".join(letters)


# Example grid as a 2D array
grid = [
    "***............",
    "  *............",
    "  *............",
    "**c**od**i**...",
    "           *..",
    "e..........*...",
    "*..........*...",
    "**m*a*g****n...",
]

# Output the result
print(collect_letters(grid))  # Expected: "codingame"

# Example grid as a 2D array
grid = [
    "***............",
    "  *............",
    "  *............",
    "**c**od**i**...",
    "           *..",
    "e..........*...",
    "*..........*...",
    "**m*a*g****n...",
]

# Output the result
print(collect_letters(grid))  # Expected: "codingame"
