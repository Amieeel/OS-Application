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
        for i in self.data:
             self.burst_time.append(i[1])
             self.arrival_time.append(i[2])
             if len(self.data[0]) == 4:
                 self.priority.append(i[3])
        print(f"Data: {self.data}")

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
        return print(f"-- FIRST COME FIRST SERVE -- \nProcess: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms")
    
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
                if self.arrival_time[i] <= time and not visited[i] and self.burst_time[i] < mininum_bursttime: #checks if ready and not visited and burst time is less than minimum
                    mininum_bursttime = self.burst_time[i] #if true, initialize its burst time as the SHORTEST job
                    index = i #save its index 
            if index == -1: # if no process was available, add time, every while loop resets it to -1 
                time+=1
                continue
            self.process.append(self.data[index][0])
            self.end_time.insert(index, (time+self.burst_time[index]))
            time += self.burst_time[index]
            visited[index] = True
            completed+=1
        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)
        return print(f"-- SHORTEST JOB FIRST -- \nProcess: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms")
        
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
                if self.arrival_time[i] <= time and 0 < remaining_time[i] < minimum_bursttime: # find ready and if it's the shortest bt
                    minimum_bursttime = remaining_time[i]
                    index = i 
                
            if index == -1:
                time += 1
                continue
            
            remaining_time[index] -= 1
            if not self.process or self.process[-1] != self.data[index][0]:
                self.process.append(self.data[index][0])

            time +=1
            if remaining_time[index] == 0:
                self.end_time[index] = time
                completed +=1
        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)
        print(f'-- SHORTEST REMAINING TIME -- \nProcess: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms')

    def NonPreemptivePriority(self):
        self.process = []
        self.end_time = []
        time = 0
        completed = 0
        visited = [False] * len(self.data)
        while completed < len(self.data):
            top_priority = float('inf')
            index = -1
            for i,p in enumerate(self.data): #loops thru all process
                if self.arrival_time[i] <= time and not visited[i] and self.priority[i] < top_priority: #checks if ready and not visited
                    top_priority = self.priority[i]
                    index = i
            if index == -1: # if no process was available, add time, every while loop resets it to -1 
                time+=1
                continue
            self.process.append(self.data[index][0])
            self.end_time.insert(index, (time+self.burst_time[index]))
            time += self.burst_time[index]
            visited[index] = True
            completed+=1
        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)
        return print(f"-- NON PREEMPTIVE PRIORITY -- \nProcess: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms")

    def PreemptivePriority(self):
        self.process = []
        self.end_time = [0] * len(self.data)
        time = 0
        completed = 0
        remaining_time = self.burst_time.copy()
        while completed < len(self.data):
            top_priority = float('inf')
            index = -1
            for i,p in enumerate(self.data):
                if self.arrival_time[i] <= time and 0 < remaining_time[i] and self.priority[i] < top_priority: # find ready and if it's top priority
                    top_priority = self.priority[i]
                    index = i 
                
            if index == -1:
                time += 1
                continue
            
            remaining_time[index] -= 1
            if not self.process or self.process[-1] != self.data[index][0]:
                self.process.append(self.data[index][0])

            time +=1
            if remaining_time[index] == 0:
                self.end_time[index] = time
                completed +=1
        self.tat = self.turnaround_time(self.end_time, self.arrival_time)
        self.wt = self.waiting_time(self.tat, self.burst_time)
        print(f'-- PREEMPTIVE PRIORITY -- Process: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms')

    def RoundRobin(self):
        self.process = []
        self.end_time = [0] * len(self.data)
        remaining_time = self.burst_time.copy()
        tq = int(input('Input Time Quantum: '))
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
                    elif 0 < remaining_time[i] < tq:
                        time += remaining_time[i]
                        remaining_time[i] = 0
                        self.process.append(self.data[i][0])
                        self.end_time[i] = time
                        completed += 1
            if not ran:
                time += 1
            self.tat = self.turnaround_time(self.end_time, self.arrival_time)
            self.wt = self.waiting_time(self.tat, self.burst_time)
            print(f'-- ROUND ROBIN -- \nProcess: {self.process} \nTurn Around Time: {self.tat}| {self.average(self.tat)}ms \nWaiting Time: {self.wt}| {self.average(self.wt)}ms')

        

    # -- TURN AROUND TIME, WAITING TIME, AVERAGE FUNCTIONS --
    def turnaround_time(self, end_time, arrival_time):
        tat_list = []
        for e,a in zip(end_time,arrival_time):
            tat_list.append(e-a)
        return tat_list

    def waiting_time(self,tat,burst_time):
        wt_list = []
        for t,b in zip(tat,burst_time):
            wt_list.append(t-b)
        return wt_list
    
    def average(self, list):
        return sum(list) / len(list)

trial = scheduling_algorithm(data2)
# trial.FCFS()
# trial.SJF()
# trial.SRT()
# trial.NonPreemptivePriority()
# trial.PreemptivePriority()
trial.RoundRobin()