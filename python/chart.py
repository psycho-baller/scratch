import matplotlib.pyplot as plt

# Data from your measurements
threads = ["1 (original)", 1, 2, 4, 6, 8, 12, 16, 24, 32]
times = [13.720, 14.858, 8.757, 4.426, 3.503, 2.909, 1.974, 1.947, 1.707, 1.579]

plt.bar(threads, times, color="skyblue")
plt.xlabel("Number of Threads")
plt.ylabel("Real Time (s)")
plt.title("Execution Time vs Number of Threads (r=50000)")
plt.show()
