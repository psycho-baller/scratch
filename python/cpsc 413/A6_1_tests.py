import matplotlib.pyplot as plt
import networkx as nx


def rec(vertex, left, right):
    # vertex is an integer between 1 and n
    # array entry left[j-1] is the index of the left child of node j
    # array entry right[j-1] is the index of the right child of node j
    # left[j-1] and right[j-1] are both zero if node j is a leaf
    vertexidx = vertex - 1
    res = [0] * 4
    if left[vertexidx] == 0:  # if left is nill, then right is nill too
        # Begin 1 - modify below only
        res = [42, 7, 13, 42]
        # res is a 4-tuple, a 4-tuple is returned
        # End 1 - modify above only
        return res
    else:
        # Begin 2 - modify below only
        res = [42, 13, 7, 42]
        # res is a 4-tuple, a 4-tuple is returned
        # End 2 - modify above only
        return res


def selected(n, root, left, right):
    # Begin 3 - modify below only
    res = rec(root, left, right)
    no_leaves = res[0] + res[3] + 42
    # no_leaves is an integer, an integer is returned
    #
    # do NOT insert any code, text, comments outside of the three Begin-End sections
    # do NOT import any additional libraries or functions
    # do NOT alter any code outside the three Begin-End sections
    # simply insert your recurrences only, within the three Begin-End sections
    # simply copy your recurrences into this template and submit it on Gradescope
    # use a 3-tuple for Problem 2, with initialization res = [0] * 3
    # End 3 - modify above only
    return no_leaves


# Helper function to compute positions for visualization using in-order traversal.
def assign_positions(vertex, depth, left, right, pos, x_counter):
    if vertex == 0:
        return
    vertex_idx = vertex - 1
    # Visit left subtree if it exists.
    if left[vertex_idx] != 0:
        assign_positions(left[vertex_idx], depth + 1, left, right, pos, x_counter)
    # Assign current vertex a position: x from the in-order counter and y = -depth.
    pos[vertex] = (x_counter[0], -depth)
    x_counter[0] += 1
    # Visit right subtree if it exists.
    if right[vertex_idx] != 0:
        assign_positions(right[vertex_idx], depth + 1, left, right, pos, x_counter)


# Function to build a directed graph from the tree arrays and visualize it.
def visualize_tree(n, root, left, right, title="Tree Visualization"):
    G = nx.DiGraph()

    # Add nodes (all nodes from 1 to n that are part of the tree).
    for i in range(1, n + 1):
        G.add_node(i)

    # Add edges from each node to its children (if they exist).
    for i in range(1, n + 1):
        if left[i - 1] != 0:
            G.add_edge(i, left[i - 1])
        if right[i - 1] != 0:
            G.add_edge(i, right[i - 1])

    # Compute positions for nodes via in-order traversal.
    pos = {}
    x_counter = [0]
    assign_positions(root, 0, left, right, pos, x_counter)

    plt.figure()
    nx.draw(
        G, pos, with_labels=True, node_size=600, node_color="lightblue", arrows=False
    )
    plt.title(title)
    plt.show()


def generate_perfect_tree(n):
    """
    Generate left and right arrays for a perfect full binary tree with n nodes.
    n should be of the form 2^(h+1)-1.
    For node i (1-indexed), left child = 2*i if 2*i <= n else 0,
    right child = 2*i+1 if 2*i+1 <= n else 0.
    """
    left = []
    right = []
    for i in range(1, n + 1):
        l = 2 * i if 2 * i <= n else 0
        r = 2 * i + 1 if 2 * i + 1 <= n else 0
        left.append(l)
        right.append(r)
    return left, right


if __name__ == "__main__":
    # --- Test Case 1: Minimal Tree (Single Node) ---
    n1 = 1
    root1 = 1
    left1 = [0]
    right1 = [0]
    result1 = selected(n1, root1, left1, right1)
    print("Test Case 1 - Expected: 1, Got:", result1)
    visualize_tree(n1, root1, left1, right1, "Test Case 1: Single Node Tree")

    # --- Test Case 2: 3-Node Full Binary Tree ---
    n2 = 3
    root2 = 1
    left2 = [2, 0, 0]
    right2 = [3, 0, 0]
    result2 = selected(n2, root2, left2, right2)
    print("Test Case 2 - Expected: 1, Got:", result2)
    visualize_tree(n2, root2, left2, right2, "Test Case 2: 3-Node Full Binary Tree")

    # --- Test Case 3: 7-Node Complete Full Binary Tree ---
    n3 = 7
    root3 = 1
    left3 = [2, 4, 6, 0, 0, 0, 0]
    right3 = [3, 5, 7, 0, 0, 0, 0]
    result3 = selected(n3, root3, left3, right3)
    print("Test Case 3 - Expected: 1, Got:", result3)
    visualize_tree(
        n3, root3, left3, right3, "Test Case 3: 7-Node Complete Full Binary Tree"
    )

    # --- Test Case 4: 9-Node Custom Full Binary Tree ---
    n4 = 9
    root4 = 1
    left4 = [2, 4, 6, 0, 8, 0, 0, 0, 0]
    right4 = [3, 5, 7, 0, 9, 0, 0, 0, 0]
    result4 = selected(n4, root4, left4, right4)
    print("Test Case 4 - Expected: 2, Got:", result4)
    visualize_tree(
        n4, root4, left4, right4, "Test Case 4: 9-Node Custom Full Binary Tree"
    )

    # --- Test Case 5: The one from the assignment ---
    n5 = 21
    root5 = 11
    left5 = [2, 0, 0, 17, 0, 4, 0, 0, 0, 0, 16, 3, 0, 0, 0, 21, 15, 19, 0, 12, 10]
    right5 = [14, 0, 0, 5, 0, 9, 0, 0, 0, 0, 18, 7, 0, 0, 0, 1, 8, 6, 0, 13, 20]
    result5 = selected(n5, root5, left5, right5)
    print("Test Case 5 - Expected: 4, Got:", result5)
    visualize_tree(n5, root5, left5, right5, "Test Case 5: the one from the assignment")

    # --- Test Case 6: Perfect Binary Tree with 15 Nodes ---
    # For a perfect binary tree of 15 nodes (nodes 1..15):
    # For node i (1 <= i <= 7), left child = 2*i and right child = 2*i+1.
    # Nodes 8..15 are leaves.
    n6 = 15
    root6 = 1
    left6 = [2, 4, 6, 8, 10, 12, 14, 0, 0, 0, 0, 0, 0, 0, 0]
    right6 = [3, 5, 7, 9, 11, 13, 15, 0, 0, 0, 0, 0, 0, 0, 0]
    # In a perfect tree, leaves are too close if chosen from the same subtree,
    # so the best valid subset is typically picking one leaf from each half.
    # Expected output: 2.
    result6 = selected(n6, root6, left6, right6)
    print("Test Case 6 - Expected: 2, Got:", result6)
    visualize_tree(
        n6, root6, left6, right6, "Test Case 6: Perfect Binary Tree (15 nodes)"
    )

    # --- Test Case 7: 5-Node Full Binary Tree ---
    # Structure:
    #       1
    #      / \
    #     2   3
    #    / \
    #   4   5
    # Leaves: 3,4,5 (all close together) so best valid subset = 1.
    n7 = 5
    root7 = 1
    left7 = [2, 4, 0, 0, 0]
    right7 = [3, 5, 0, 0, 0]
    result7 = selected(n7, root7, left7, right7)
    print("Test Case 7 - Expected: 1, Got:", result7)
    visualize_tree(n7, root7, left7, right7, "Test Case 7: 5-Node Full Binary Tree")

    # --- Test Case 8: Another 9-Node Full Binary Tree ---
    # Structure:
    #       1
    #      / \
    #     2   3
    #    / \  / \
    #   4  5 6  7
    #  / \
    # 8   9
    # Leaves: 5,6,7,8,9. Expected: 2.
    n8 = 9
    root8 = 1
    left8 = [2, 4, 6, 8, 0, 0, 0, 0, 0]
    right8 = [3, 5, 7, 9, 0, 0, 0, 0, 0]
    result8 = selected(n8, root8, left8, right8)
    print("Test Case 8 - Expected: 2, Got:", result8)
    visualize_tree(
        n8, root8, left8, right8, "Test Case 8: 9-Node Full Binary Tree (Alternate)"
    )

    # --- Test Case 9: Perfect Binary Tree with 31 Nodes ---
    n9 = 31  # 2^(5)-1 = 31, perfect tree of height 4.
    root9 = 1
    left9, right9 = generate_perfect_tree(n9)
    result9 = selected(n9, root9, left9, right9)
    print("Test Case 9 - Expected: 4, Got:", result9)
    visualize_tree(
        n9, root9, left9, right9, "Test Case 9: Perfect Binary Tree (31 nodes)"
    )

    # --- Test Case 10: Perfect Binary Tree with 63 Nodes ---
    n10 = 63  # 2^(6)-1 = 63, perfect tree of height 5.
    root10 = 1
    left10, right10 = generate_perfect_tree(n10)
    result10 = selected(n10, root10, left10, right10)
    print("Test Case 10 - Expected: 8, Got:", result10)
    visualize_tree(
        n10, root10, left10, right10, "Test Case 10: Perfect Binary Tree (63 nodes)"
    )

    # --- Test Case 11: 11-Node Full Binary Tree (Different Shape) ---
    # Structure:
    #         1
    #        /  \
    #       2    3
    #      / \
    #     4   5
    #    /   /  \
    #   8   10  11
    #  (Also, 3 has children 6 and 7.)
    # Internal nodes: 1,2,3,4,5; Leaves: 6,7,8,10,11.
    n11 = 11
    root11 = 1
    left11 = [2, 4, 6, 8, 10, 0, 0, 0, 0, 0, 0]
    right11 = [3, 5, 7, 9, 11, 0, 0, 0, 0, 0, 0]
    result11 = selected(n11, root11, left11, right11)
    print("Test Case 11 - Expected: 2, Got:", result11)
    visualize_tree(
        n11,
        root11,
        left11,
        right11,
        "Test Case 11: 11-Node Full Binary Tree (Different Shape)",
    )

    # --- Test Case 12: 15-Node Full Binary Tree (Left-Heavy) ---
    # Structure:
    #         1
    #       /   \
    #      2     3
    #     / \   / \
    #    4   5 6   7
    #   / \  / \
    #  8  9 10 11
    # And then make 6 internal: children 12,13; and 7 internal: children 14,15.
    n12 = 15
    root12 = 1
    left12 = [2, 4, 6, 8, 10, 12, 14, 0, 0, 0, 0, 0, 0, 0, 0]
    right12 = [3, 5, 7, 9, 11, 13, 15, 0, 0, 0, 0, 0, 0, 0, 0]
    result12 = selected(n12, root12, left12, right12)
    print("Test Case 12 - Expected: 2, Got:", result12)
    visualize_tree(
        n12,
        root12,
        left12,
        right12,
        "Test Case 12: 15-Node Full Binary Tree (Left-Heavy)",
    )

    # --- Test Case 13: 9-Node Full Binary Tree (Deep Right Branch) ---
    # Structure:
    #         1
    #       /   \
    #      2     3
    #     / \   / \
    #    4   5 6   7
    #            /  \
    #           9    8
    # Here, node 3’s right child (7) is replaced by an internal node with children 8 and 9.
    n13 = 9
    root13 = 1
    # Define: 1: children 2,3; 2: children 4,5; 3: children 6,7; 7: children 8,9.
    left13 = [2, 4, 6, 0, 0, 0, 8, 0, 0]
    right13 = [3, 5, 7, 0, 0, 0, 9, 0, 0]
    result13 = selected(n13, root13, left13, right13)
    print("Test Case 13 - Expected: 2, Got:", result13)
    visualize_tree(
        n13,
        root13,
        left13,
        right13,
        "Test Case 13: 9-Node Full Binary Tree (Deep Right Branch)",
    )

    # --- Test Case 14: 17-Node Full Binary Tree ---
    # Structure:
    #         1
    #       /   \
    #      2     3
    #     / \   / \
    #    4   5 6   7
    #   /    /     / \
    #  8    10    14  15
    #  and: 4: children 8,9; 5: children 10,11; 6: children 12,13; 7: children 14,15; then 8 internal: children 16,17.
    n14 = 17
    root14 = 1
    left14 = [2, 4, 6, 8, 10, 12, 14, 16, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    right14 = [3, 5, 7, 9, 11, 13, 15, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    result14 = selected(n14, root14, left14, right14)
    print("Test Case 14 - Expected: 3, Got:", result14)
    visualize_tree(
        n14, root14, left14, right14, "Test Case 14: 17-Node Full Binary Tree"
    )

    # --- Test Case 15: 25-Node Full Binary Tree ---
    # Structure:
    # Build a full binary tree with 25 nodes.
    # 1: children 2,3;
    # 2: children 4,5; 3: children 6,7;
    # 4: children 8,9; 5: children 10,11; 6: children 12,13; 7: children 14,15;
    # 8: children 16,17; 9: children 18,19; 10: children 20,21; 11: children 22,23; 12: children 24,25.
    n15 = 25
    root15 = 1
    left15 = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24] + [0] * (25 - 12)
    right15 = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25] + [0] * (25 - 12)
    result15 = selected(n15, root15, left15, right15)
    print("Test Case 15 - Expected: 4, Got:", result15)
    visualize_tree(
        n15, root15, left15, right15, "Test Case 15: 25-Node Full Binary Tree"
    )

    n16 = 7
    root16 = 1
    left16 = [2, 0, 4, 0, 6, 0, 0]
    right16 = [3, 0, 5, 0, 7, 0, 0]
    result16 = selected(n16, root16, left16, right16)
    print("Test Case 13 - Expected: 1, Got:", result16)
    visualize_tree(
        n16,
        root16,
        left16,
        right16,
        "Test Case 16: 9-Node Full Binary Tree (Deep Right Branch)",
    )
