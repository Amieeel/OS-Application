class PageReplacement:
    def __init__(self, capacity):
        self.capacity = capacity
        self.frames = []
        self.ref_bits = {} 
        self.pointer = 0   
        self.counts = {}
        self.history = []

    def fifo(self, page):
        """First-In, First-Out: Replace the oldest page."""
        if page not in self.frames:
            if len(self.frames) < self.capacity:
                self.frames.append(page)
            else:
                self.frames.pop(0) # Oldest out
                self.frames.append(page)
            return list(self.frames), True
        return list(self.frames), False

    def optimal(self, page, future_references):
        """Optimal: Replace page that will not be used for the longest time."""
        if page in self.frames:
            return list(self.frames), False
        
        if len(self.frames) < self.capacity:
            self.frames.append(page)
        else:
            farthest = -1
            to_replace = -1
            for f in self.frames:
                try:
                    idx = future_references.index(f)
                except ValueError:
                    idx = float('inf') 
                
                if idx > farthest:
                    farthest = idx
                    to_replace = f
            self.frames.remove(to_replace)
            self.frames.append(page)
        return list(self.frames), True

    def lru(self, page):
        is_fault = False
        if page not in self.frames:
            is_fault = True
            if len(self.frames) < self.capacity:
                self.frames.append(page)
            else:
                # Use self.history instead of a passed argument
                lru_page = self.history.pop(0) 
                self.frames.remove(lru_page)
                self.frames.append(page)
        
        # Update self.history
        if page in self.history: self.history.remove(page)
        self.history.append(page)
        return list(self.frames), is_fault
    
    def lru_approximation(self, page):
        """LRU Approximation (e.g., Second Chance/Clock)."""
        if page in self.frames:
            self.ref_bits[page] = 1
            return list(self.frames), False

        if len(self.frames) < self.capacity:
            self.frames.append(page)
            self.ref_bits[page] = 1
        else:
            while True:
                candidate = self.frames[self.pointer]
                if self.ref_bits[candidate] == 0:
                    self.frames[self.pointer] = page
                    self.ref_bits[page] = 1
                    self.pointer = (self.pointer + 1) % self.capacity
                    break
                else:
                    self.ref_bits[candidate] = 0
                    self.pointer = (self.pointer + 1) % self.capacity
        return list(self.frames), True

    def lfu(self, page):
        """Least Frequently Used (Counting-based)."""
        self.counts[page] = self.counts.get(page, 0) + 1
        
        if page in self.frames:
            return list(self.frames), False
        
        if len(self.frames) < self.capacity:
            self.frames.append(page)
        else:
            victim = min(self.frames, key=lambda p: self.counts[p])
            self.frames.remove(victim)
            self.frames.append(page)
        return list(self.frames), True
 

class PageReplacementManager:
    def __init__(self, capacity, algorithm_type):
        self.capacity = capacity
        self.algo = algorithm_type
        self.visualizer = PageReplacement(capacity)
        self.hits = 0
        self.faults = 0
        self.results = [] 

    def run(self, pages, future_refs=None):
        print(f"\n--- Running {self.algo.upper()} Simulation ---")
        
        for i, page in enumerate(pages):
            args = [page]
            if self.algo == 'optimal':
                args.append(future_refs[i+1:] if future_refs else [])
            
          
            method = getattr(self.visualizer, self.algo)
            frames, is_fault = method(*args)
            
          
            status = "Fault" if is_fault else "Hit"
            if is_fault:
                self.faults += 1
            else:
                self.hits += 1
                
            self.results.append({'page': page, 'frames': list(frames), 'status': status})
            print(f"Page: {page:2} | Frames: {str(frames):15} | Fault: {is_fault}")
        
        self.print_summary()

    def step(self, page, future_references=None):
        method = getattr(self.visualizer, self.algo)
        args = [page]
        if self.algo == 'optimal': args.append(future_references)
        
        frames, is_fault = method(*args)
        
        # Track stats
        if is_fault: self.faults += 1
        else: self.hits += 1
        
        self.results.append({'page': page, 'frames': list(frames), 'status': 'Fault' if is_fault else 'Hit'})
        return frames, is_fault

    def print_summary(self):
        total = self.hits + self.faults
        print("-" * 45)
        print(f"Total Page Accesses: {total}")
        print(f"Total Page Hits    : {self.hits}")
        print(f"Total Page Faults  : {self.faults}")
        print(f"Hit Ratio          : {(self.hits/total)*100:.2f}%")

def main():
    # 1. Setup
    capacity = int(input("Enter frame capacity: "))
    algo = input("Choose an algorithm (fifo, lru, clock, lfu, optimal): ").lower()
    pages_input = input("Enter page references (e.g., 3,4,2,3): ")
    pages = [int(p.strip()) for p in pages_input.split(',') if p.strip()]

    # 2. Execution
    manager = PageReplacementManager(capacity, algo)
    
    # CALL RUN() instead of a loop calling step()
    manager.run(pages, future_refs=pages if algo == 'optimal' else None)
    
    # 3. Print Summary
    print(f"\nSimulation Complete. Hits: {manager.hits}, Faults: {manager.faults}")

if __name__ == "__main__":
    main()
