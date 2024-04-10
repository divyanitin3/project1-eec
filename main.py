class CacheLine:
    def __init__(self):
        self.valid = False
        self.tag = None
        self.data = [None] * 64  # Assuming data size is equivalent to the cache line size

class DirectMappedCache:
    def __init__(self, size_kb, line_size, access_time, idle_power, active_power):
        self.size_kb = size_kb
        self.line_size = line_size
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.num_lines = (size_kb * 1024) // line_size
        self.lines = [CacheLine() for _ in range(self.num_lines)]
        self.energy_consumed = 0

    def access(self, address, mode):
        # Implement direct-mapped cache access logic here
        pass

class SetAssociativeCache:
    def __init__(self, size_kb, line_size, assoc, access_time, idle_power, active_power, transfer_penalty):
        self.size_kb = size_kb
        self.line_size = line_size
        self.assoc = assoc
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.transfer_penalty = transfer_penalty
        self.sets = [[CacheLine() for _ in range(assoc)] for _ in range((size_kb * 1024) // (line_size * assoc))]
        self.energy_consumed = 0

    def access(self, address, mode):
        # Implement set-associative cache access logic here
        pass

class DRAM:
    def __init__(self, size_gb, access_time, idle_power, active_power, transfer_penalty):
        self.size_gb = size_gb
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.transfer_penalty = transfer_penalty
        self.energy_consumed = 0

    def access(self, address, mode):
        # Implement DRAM access logic here
        pass

# Initializing caches and DRAM with the provided specifications
l1_instruction_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l1_data_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=4, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5)
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)

def simulate(trace_file):
    # Implementation of the simulation loop
    pass

# This is just a structural update; you'll need to implement the logic for accessing and managing caches and DRAM based on your project requirements.
