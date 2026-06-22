# content_data.py

ABOUT_CONTENT = {
    "app_information": {
        "app_name": "GO Rhythm (Ready, Set, GO!)",
        "app_description": """Visualizes and simulates different algorithms according to CPU scheduling, 
memory allocation, virtual memory, and disk scheduling in modern operating systems. 
This educational tool allows users to input custom parameters, step through the execution of 
various OS algorithms, and observe real-time visual feedback and computed metrics. 
It is designed to bridge the gap between theoretical OS concepts and practical, mechanical understanding."""
    },
    "algorithm_descriptions": {
        "cpu_scheduling": "In a multiprogramming system, the OS decides which process uses the CPU.",
        "memory_allocation": "Main memory must accommodate both the OS and user processes efficiently.",
        "virtual_memory": "Virtual memory allows a computer to run processes larger than physical RAM.",
        "disk_scheduling": "Manages the movement of the disk head to minimize seek time."
    }
}

LEARN_CONTENT = {
    "cpu_scheduling": {
        "title": "CPU Scheduling Algorithms",
        "how_it_works": """Inputs: You provide a list of processes along with Arrival Times, Burst Times, 
Priorities, and a Time Quantum. 
Visualization: The app generates a live Gantt Chart, displaying exactly which process 
occupies the CPU at any given millisecond. 
Simulation: Step through time to watch processes arrive, preempt, and finish."""
    },
    "memory_allocation": {
        "title": "Memory Management",
        "how_it_works": """Inputs: Define the Total Memory size, OS size, and a queue of incoming jobs.
Visualization: A dynamic Memory Map draws the memory blocks, showing where the OS lives, 
where user processes are loaded, and where free "holes" exist.
Simulation: Watch algorithms like First Fit, Best Fit, Worst Fit, and Next Fit hunt for 
appropriate holes and track fragmentation levels."""
    },
    "virtual_memory": {
        "title": "Virtual Memory Management",
        "how_it_works": """Inputs: Input a Reference String (page sequence) and number of available physical Frames.
Visualization: The app displays a Frame Grid, visually filling slots as pages are loaded 
and highlighting when a page is swapped out.
Simulation: The app flags Page Faults vs. Page Hits and simulates algorithms like FIFO, 
Optimal, and LRU to calculate the total Page Fault Rate."""
    },
    "disk_scheduling": {
        "title": "Disk Scheduling Algorithms",
        "how_it_works": """Inputs: Provide the starting head position, total cylinders, and request queue.
Visualization: The app plots a path diagram showing the physical movement of the disk head.
Simulation: Simulates FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK to compute total 
Head Movement (Seek Time) for efficiency comparison."""
    }
}