def fcfs(requests, head):
    sequence = [head] + list(requests)
    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def sstf(requests, head):
    remaining = list(requests)
    sequence = [head]
    current = head

    while remaining:
        closest = min(remaining, key=lambda x: abs(x - current))
        sequence.append(closest)
        remaining.remove(closest)
        current = closest

    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def scan(requests, head, disk_size):
    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    sequence = [head] + left + [0] + right

    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def cscan(requests, head, disk_size):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    sequence = [head] + right + [disk_size - 1, 0] + left

    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def look(requests, head):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    sequence = [head] + right + list(reversed(left))

    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def clook(requests, head):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    sequence = [head] + right + left

    total = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence)-1))
    return sequence, total


def show_head_movement_calculation(sequence):
    print("\nComputing for the total head movement:\n")

    total = 0

    for i in range(len(sequence) - 1):
        start = sequence[i]
        end = sequence[i + 1]
        movement = abs(end - start)

        print(
            f"from {start} to {end} = "
            f"{max(start, end)} - {min(start, end)} = {movement}"
        )

        total += movement

    print(f"\nTotal head movement = {total} tracks\n")


def get_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"Enter a value >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"Enter a value <= {max_val}")
                continue
            return val
        except ValueError:
            print("Invalid input.")


def get_requests(disk_size):
    while True:
        try:
            req = list(map(int, input("Enter requests separated by spaces: ").split()))
            if all(0 <= r < disk_size for r in req):
                return req
            print("Request out of range.")
        except ValueError:
            print("Invalid input.")


def run_simulation():
    print("=" * 50)
    print("DISK SCHEDULING SIMULATOR")
    print("=" * 50)

    disk_size = get_int("Disk size: ", min_val=10)
    head = get_int(f"Initial head position (0-{disk_size-1}): ", 0, disk_size - 1)
    requests = get_requests(disk_size)

    print("\n1. FCFS")
    print("2. SSTF")
    print("3. SCAN")
    print("4. C-SCAN")
    print("5. LOOK")
    print("6. C-LOOK")
    print("7. ALL")

    choice = get_int("Choice: ", 1, 7)

    results = {
        1: [("FCFS", fcfs(requests, head))],
        2: [("SSTF", sstf(requests, head))],
        3: [("SCAN", scan(requests, head, disk_size))],
        4: [("C-SCAN", cscan(requests, head, disk_size))],
        5: [("LOOK", look(requests, head))],
        6: [("C-LOOK", clook(requests, head))],
        7: [
            ("FCFS", fcfs(requests, head)),
            ("SSTF", sstf(requests, head)),
            ("SCAN", scan(requests, head, disk_size)),
            ("C-SCAN", cscan(requests, head, disk_size)),
            ("LOOK", look(requests, head)),
            ("C-LOOK", clook(requests, head))
        ]
    }

    for name, (sequence, total) in results[choice]:
        print("\n" + "=" * 50)
        print(name)
        print("=" * 50)
        print("Sequence:", " -> ".join(map(str, sequence)))
        show_head_movement_calculation(sequence)

    if choice == 7:
        print("=" * 40)
        print(f"{'Algorithm':<10} {'Total Movement':>15}")
        print("=" * 40)

        for name, (_, total) in results[7]:
            print(f"{name:<10} {total:>15}")

        print("=" * 40)

def main():
    while True:
        run_simulation()

        print("\n + "=" *50)
        again = input("Do you want to run another simulation? (yes/no): ").strip()>lower()

        if again not in ("yes", "y"):
            print("\nThank you for using the Disk Scheduling Visualizer!")
            print("Goodbye!")
            break 
        print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    main()
