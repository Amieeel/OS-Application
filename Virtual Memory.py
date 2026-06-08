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
        self.type = algorithm_type # 'fifo', 'lru', 'clock', 'lfu', 'optimal'
        self.visualizer = PageReplacement(capacity) 
        
    def step(self, page, future_references=None):
        if self.type == 'fifo':
            return self.visualizer.fifo(page)
        elif self.type == 'lru':
            return self.visualizer.lru(page)
        elif self.type == 'clock':
            return self.visualizer.clock_algorithm(page)
        elif self.type == 'lfu':
            return self.visualizer.lfu(page)
        elif self.type == 'optimal':
            return self.visualizer.optimal(page, future_references)
        

def main():
    try:
        capacity = int(input("Enter frame capacity: "))
    except ValueError:
        print("Capacity must be an integer.")
        return

    print("Available algorithms: fifo, lru, clock, lfu, optimal")
    algo = input("Choose an algorithm: ").lower()

    pages_input = input("Enter page references (comma-separated, e.g., 7,0,1,2,0,3): ")
    pages = [int(p.strip()) for p in pages_input.split(',')]

    future_refs = None
    if algo == 'optimal':
        future_refs = pages 
    manager = PageReplacementManager(capacity, algo)
    
    print(f"\n--- Running {algo.upper()} Simulation ---")
    for i, page in enumerate(pages):
        args = [page]
        if algo == 'optimal':
            args.append(pages[i+1:])
            
        frames, is_fault = manager.step(*args)
        print(f"Page: {page:2} | Frames: {str(frames):15} | Fault: {is_fault}")

if __name__ == "__main__":
    main()

