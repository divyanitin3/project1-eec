import random
class MemorySubsystem:
    def __init__(self, l1_instruction_cache, l1_data_cache, l2_cache, dram):
        self.l1_instruction_cache = l1_instruction_cache
        self.l1_data_cache = l1_data_cache
        self.l2_cache = l2_cache
        self.dram = dram
        self.time_ns = 0  # Current time in nanoseconds
        
        self.l1_instruction_hits = 0
        self.l1_instruction_misses = 0
        self.l1_data_hits = 0
        self.l1_data_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.dram_accesses = 0  # Every DRAM access is a "miss" from cache perspective

        
    def calculate_idle_energy(self):
        # Calculate the total simulation time in seconds
        total_time_s = self.time_ns * 1e-9

        # Calculate idle energy for each component
        # Note: This example assumes that energy_consumed_pj attributes are reset to zero at the start of the simulation
        # and only include active energy consumption during accesses.
        self.l1_instruction_cache.energy_consumed_pj += (self.l1_instruction_cache.idle_power_w * total_time_s) * 1e12
        self.l1_data_cache.energy_consumed_pj += (self.l1_data_cache.idle_power_w * total_time_s) * 1e12
        self.l2_cache.energy_consumed_pj += (self.l2_cache.idle_power_w * total_time_s) * 1e12
        self.dram.energy_consumed_pj += (self.dram.idle_power_w * total_time_s) * 1e12
    
    def calculate_performance_metrics(self):
        # Calculate and print performance metrics at the end of the simulation
        total_hits = self.l1_instruction_hits + self.l1_data_hits + self.l2_hits
        total_misses = self.l1_instruction_misses + self.l1_data_misses + self.l2_misses
        total_accesses = total_hits + total_misses
        total_energy = self.l1_instruction_cache.energy_consumed_pj + self.l1_data_cache.energy_consumed_pj + \
                       self.l2_cache.energy_consumed_pj + self.dram.energy_consumed_pj
        average_access_time_ns = self.time_ns / total_accesses if total_accesses else 0

        print(f"Total Hits: {total_hits}")
        print(f"Total Misses: {total_misses}")
        print(f"L1 Instruction Cache Hits: {self.l1_instruction_hits}, Misses: {self.l1_instruction_misses}")
        print(f"L1 Data Cache Hits: {self.l1_data_hits}, Misses: {self.l1_data_misses}")
        print(f"L2 Cache Hits: {self.l2_hits}, Misses: {self.l2_misses}")
        print(f"DRAM Accesses: {self.dram_accesses}")
        print(f"Total Energy Consumed (pJ): {total_energy}")
        print(f"Average Access Time (ns): {average_access_time_ns}")


    def access_memory(self, address, mode, is_instruction=False):
        # Modify this method to increment hit/miss counters based on the access results
        target_cache = self.l1_instruction_cache if is_instruction else self.l1_data_cache
        hit, time_taken, energy_consumed = target_cache.access(address, mode)

        if is_instruction:
            if hit:
                self.l1_instruction_hits += 1
            else:
                self.l1_instruction_misses += 1
        else:
            if hit:
                self.l1_data_hits += 1
            else:
                self.l1_data_misses += 1

        if not hit:
            # L2 cache access if L1 miss
            hit, l2_time, l2_energy = self.l2_cache.access(address, mode)
            if hit:
                self.l2_hits += 1
            else:
                self.l2_misses += 1
                self.dram_accesses += 1  # Increment DRAM access on L2 miss
        
        if not hit:
            # L2 cache access if L1 miss
            hit, l2_time, l2_energy = self.l2_cache.access(address, mode)
            time_taken += l2_time
            energy_consumed += l2_energy
            
            if not hit:
                # DRAM access if L2 miss
                _, dram_time, dram_energy = self.dram.access(address, mode)
                time_taken += dram_time
                energy_consumed += dram_energy
        
        self.time_ns += time_taken
        return hit, time_taken, energy_consumed

    def simulate(self, trace_file):
        # Read and process the trace file to simulate memory accesses
        self.calculate_idle_energy()


class CacheLine:
    def __init__(self):
        self.valid = False
        self.tag = None
        self.data = [None] * 64  # Assuming data size is equivalent to the cache line size

class DirectMappedCache:
    def __init__(self, size_kb, line_size, access_time_ns, idle_power_w, active_power_w):
        self.size_kb = size_kb
        self.line_size = line_size
        self.access_time_ns = access_time_ns
        self.idle_power_w = idle_power_w
        self.active_power_w = active_power_w
        self.num_lines = (size_kb * 1024) // line_size
        self.lines = [CacheLine() for _ in range(self.num_lines)]
        self.energy_consumed_pj = 0  # Energy consumed in picojoules

    def access(self, address, mode):
        index = (address // self.line_size) % self.num_lines
        tag = address // (self.line_size * self.num_lines)
        line = self.lines[index]

        # Calculate active energy consumed for this access
        energy_per_access_pj = (self.active_power_w * (self.access_time_ns * 1e-9)) * 1e12
        self.energy_consumed_pj += energy_per_access_pj

        if line.valid and line.tag == tag:
            # Cache hit
            hit = True
        else:
            # Cache miss
            hit = False

            if mode == 'write':
                # For write misses, simulate a read operation first to bring the entire cache line into cache
                # This simulates bringing data into the cache before it is modified (write-allocate policy)
                # Note: In a real implementation, this might involve invoking a lower memory level's access method.
                # For simplicity, we'll just account for the additional time and energy here without actual data movement.
                self.energy_consumed_pj += energy_per_access_pj  # Additional energy for the read before write
                self.time_ns += self.access_time_ns  # Additional time for the read before write
            
            # Update the cache line (applicable for both read and write misses)
            line.valid = True
            line.tag = tag

        return hit, self.access_time_ns, energy_per_access_pj



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
        set_index = (address // self.line_size) % len(self.sets)
        tag = address // (self.line_size * len(self.sets))
        cache_set = self.sets[set_index]

        # Initially assume a miss
        hit = False
        energy_per_access_pj = (self.active_power_w * (self.access_time_ns * 1e-9)) * 1e12

        # Search for the tag within the set
        for line in cache_set:
            if line.valid and line.tag == tag:
                hit = True
                # If it's a hit, no need to replace a cache line, just consume energy for access
                self.energy_consumed += energy_per_access_pj
                break

        if not hit:
            # Cache miss
            # Select a line for replacement based on the replacement policy (random in this case)
            line_to_update = random.choice(cache_set)
            
            # For write misses, the read before write policy implies an additional read operation
            if mode == 'write':
                # Double the energy for read before write operation
                energy_per_access_pj *= 2

            # Update the cache line
            line_to_update.valid = True
            line_to_update.tag = tag
            # The actual data movement isn't simulated, but energy for fetching the data is accounted for

            self.energy_consumed += energy_per_access_pj

        return hit, self.access_time_ns, energy_per_access_pj


class DRAM:
    def __init__(self, size_gb, access_time_ns, idle_power_w, active_power_w, transfer_penalty_pj):
        self.size_gb = size_gb
        self.access_time_ns = access_time_ns
        self.idle_power_w = idle_power_w
        self.active_power_w = active_power_w
        self.transfer_penalty_pj = transfer_penalty_pj
        self.energy_consumed_pj = 0  # Energy consumed in picojoules

    def access(self, address, mode):
        # All DRAM accesses are treated as misses since there's no "hit" concept in DRAM

        # Calculate energy consumed for this access
        # Active energy: Convert power consumption (watts) to energy (joules) based on access time (seconds),
        # then convert joules to picojoules (1 joule = 1e12 picojoules)
        active_energy_pj = (self.active_power_w * (self.access_time_ns * 1e-9)) * 1e12

        # Add transfer penalty for accessing DRAM
        total_energy_pj = active_energy_pj + self.transfer_penalty_pj

        # Update total energy consumed
        self.energy_consumed_pj += total_energy_pj

        # DRAM access is always considered a miss, so there's no 'hit' variable
        return False, self.access_time_ns, total_energy_pj

# Initializing caches and DRAM with the provided specifications
l1_instruction_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l1_data_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=4, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5)
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)

memory_system = MemorySubsystem(l1_instruction_cache, l1_data_cache, l2_cache, dram)
# Here you would call `memory_system.simulate("your_trace_file.din")`

