# process, burst time, arrival time
data0 = [["P1",2,0], ["P2",4,3], ["P3", 2, 4], ["P4", 6, 5]]
data1 = [["P1",3,0,1],["P2",5,2,3],["P3",2,4,4],["P4",4,6,2]]
data2 = [["P1",6,0],["P2",2,0],["P3",8,0],["P4",3,0]]
data3 = [["P1",4,0],["P2",3,6],["P3",2,8],["P4",5,12]]
data4 = [["P1",10,0],["P2",2,2],["P3",1,3],["P4",2,5]]
data5 = [["P1",3,0],["P2",4,5],["P3",2,10],["P4",1,15]]
data6 = [["P1",5,0],["P2",3,1],["P3",8,2],["P4",6,3],["P5",2,4]]
data7 = [["P1",20,0],["P2",2,1],["P3",3,2],["P4",1,3]]
data8 = [["P1",7,0],["P2",5,2],["P3",3,4],["P4",1,5],["P5",2,6],["P6",8,7]]
data9 = [["P1",1,0],["P2",2,1],["P3",1,2],["P4",2,3],["P5",1,4],["P6",2,5]]
data10 = [["P1",5,0]]


class scheduling_algorithm:
    def __init__(self, data):
        self.data = data
        self.burst_time = []
        self.arrival_time = []
        self.priority = []

        for p in self.data:
            self.burst_time.append(p[1])
            self.arrival_time.append(p[2])

            # always include priority slot
            if len(p) >= 4:
                self.priority.append(p[3])
            else:
                self.priority.append(None)

        print(f"Data: {self.data}")

    # ---------------- FCFS ----------------
    def FCFS(self): #Non-Preemptive
        self.process = []
        self.end_time = []

        for i,p in enumerate(self.data):
            self.process.append(p[0])

            burst = p[1]
            arrival = p[2]

            if i == 0:
                start = arrival
            else:
                start = max(self.end_time[-1], arrival)

            end = start + burst
            self.end_time.append(end)

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
        "algorithm": "FCFS",
        "process": self.process,
        "tat": self.tat,
        "wt": self.wt,
        "avg_tat": self.average(self.tat),
        "avg_wt": self.average(self.wt),
        }

    # ---------------- SJF ----------------
    def SJF(self): #Non-preemptive
        self.process = []
        self.end_time = []

        time = 0
        completed = 0
        visited = [False] * len(self.data)

        while completed < len(self.data):
            mininum_bursttime = float('inf')
            index = -1

            for i,p in enumerate(self.data): #loops thru all process
                if self.arrival_time[i] <= time and not visited[i] and self.burst_time[i] < mininum_bursttime:
                    mininum_bursttime = self.burst_time[i]
                    index = i

            if index == -1:
                time += 1
                continue

            self.process.append(self.data[index][0])

            # FIX: no insert (breaks indexing)
            self.end_time.append(time + self.burst_time[index])

            time += self.burst_time[index]
            visited[index] = True
            completed += 1

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
        "algorithm": "SJF",
        "process": self.process,
        "tat": self.tat,
        "wt": self.wt,
        "avg_tat": self.average(self.tat),
        "avg_wt": self.average(self.wt),
        }

    # ---------------- SRT ----------------
    def SRT(self): #Preemptive
        self.process = []
        self.end_time = [0] * len(self.data)

        time = 0
        completed = 0
        remaining_time = self.burst_time.copy()

        while completed < len(self.data):
            minimum_bursttime = float('inf')
            index = -1

            for i,p in enumerate(self.data):
                if self.arrival_time[i] <= time and 0 < remaining_time[i] < minimum_bursttime:
                    minimum_bursttime = remaining_time[i]
                    index = i

            if index == -1:
                time += 1
                continue

            remaining_time[index] -= 1

            if not self.process or self.process[-1] != self.data[index][0]:
                self.process.append(self.data[index][0])

            time += 1

            if remaining_time[index] == 0:
                self.end_time[index] = time
                completed += 1

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
        "algorithm": "SRT",
        "process": self.process,
        "tat": self.tat,
        "wt": self.wt,
        "avg_tat": self.average(self.tat),
        "avg_wt": self.average(self.wt),
        }

    # ---------------- NON PREEMPTIVE PRIORITY ----------------
    def NonPreemptivePriority(self):
        self.process = []
        self.end_time = []

        time = 0
        completed = 0
        visited = [False] * len(self.data)

        while completed < len(self.data):
            best = float('inf')
            index = -1

            for i in range(len(self.data)):

                if self.arrival_time[i] <= time and not visited[i]:
                    if self.priority[i] is not None and self.priority[i] < best:
                        best = self.priority[i]
                        index = i

            if index == -1:
                time += 1
                continue

            self.process.append(self.data[index][0])

            # FIX: avoid insert
            self.end_time.append(time + self.burst_time[index])

            time += self.burst_time[index]
            visited[index] = True
            completed += 1

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
            "algorithm": "NonPreemptivePriority",
            "process": self.process,
            "tat": self.tat,
            "wt": self.wt,
            "avg_tat": self.average(self.tat),
            "avg_wt": self.average(self.wt)
        }

    # ---------------- PREEMPTIVE PRIORITY ----------------
    def PreemptivePriority(self):
        self.process = []
        self.end_time = [0] * len(self.data)
        remaining = self.burst_time.copy()

        time = 0
        completed = 0

        while completed < len(self.data):
            best = float('inf')
            index = -1

            for i in range(len(self.data)):
                if (
                    self.arrival_time[i] <= time and
                    remaining[i] > 0 and
                    self.priority[i] is not None and
                    self.priority[i] < best
                ):
                    best = self.priority[i]
                    index = i

            if index == -1:
                time += 1
                continue

            remaining[index] -= 1

            if not self.process or self.process[-1] != self.data[index][0]:
                self.process.append(self.data[index][0])

            time += 1

            if remaining[index] == 0:
                self.end_time[index] = time
                completed += 1

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
            "algorithm": "PreemptivePriority",
            "process": self.process,
            "tat": self.tat,
            "wt": self.wt,
            "avg_tat": self.average(self.tat),
            "avg_wt": self.average(self.wt)
        }

    # ---------------- HELPER ----------------
    def is_better_priority(self, i, best_priority):
        if self.priority[i] is None:
            return False
        return self.priority[i] < best_priority

    def RoundRobin(self, tq):
        self.process = []
        self.end_time = [0] * len(self.data)
        remaining_time = self.burst_time.copy()

        time = 0
        completed = 0

        while completed < len(self.data):
            ran = False

            for i, p in enumerate(self.data):
                if self.arrival_time[i] <= time and remaining_time[i] > 0:
                    ran = True

                    if remaining_time[i] >= tq:
                        remaining_time[i] -= tq
                        time += tq
                        self.process.append(self.data[i][0])

                        if remaining_time[i] == 0:
                            self.end_time[i] = time
                            completed += 1

                    else:
                        time += remaining_time[i]
                        remaining_time[i] = 0
                        self.process.append(self.data[i][0])
                        self.end_time[i] = time
                        completed += 1

            if not ran:
                time += 1

        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)

        return {
            "algorithm": "RoundRobin",
            "process": self.process,
            "tat": self.tat,
            "wt": self.wt,
            "avg_tat": self.average(self.tat),
            "avg_wt": self.average(self.wt),
        }

    # ---------------- METRICS ----------------
    def turnaround_time(self, end_time, arrival_time):
        return [e - a for e, a in zip(end_time, arrival_time)]

    def waiting_time(self, tat, burst_time):
        return [t - b for t, b in zip(tat, burst_time)]

    def average(self, list):
        return sum(list) / len(list)


trial = scheduling_algorithm(data2)
trial.RoundRobin(2)