import random
import subprocess
import os


class MemorySubsystem:
    def __init__(self, l1_instruction_cache, l1_data_cache, l2_cache, dram):
        self.l1_instruction_cache = l1_instruction_cache
        self.l1_data_cache = l1_data_cache
        self.l2_cache = l2_cache
        self.dram = dram
        self.time_ns = 0 
        self.l1_instruction_hits = 0
        self.l1_instruction_misses = 0
        self.l1_data_hits = 0
        self.l1_data_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.dram_accesses = 0

        
    def calculate_idle_energy(self):
        # Calculate the total simulation time in seconds
        total_time_s = self.time_ns * 1e-9

        self.l1_instruction_cache.energy_consumed += (self.l1_instruction_cache.idle_power * total_time_s) * 1e12
        self.l1_data_cache.energy_consumed += (self.l1_data_cache.idle_power * total_time_s) * 1e12
        self.l2_cache.energy_consumed += (self.l2_cache.idle_power * total_time_s) * 1e12
        self.dram.energy_consumed += (self.dram.idle_power * total_time_s) * 1e12
    
    def calculate_performance_metrics(self):
        total_hits = self.l1_instruction_hits + self.l1_data_hits + self.l2_hits
        total_misses = self.l1_instruction_misses + self.l1_data_misses + self.l2_misses
        total_accesses = total_hits + total_misses
        total_energy = self.l1_instruction_cache.energy_consumed + self.l1_data_cache.energy_consumed + \
                       self.l2_cache.energy_consumed + self.dram.energy_consumed
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
            hit, l2_time, l2_energy = self.l2_cache.access(address, mode)
            time_taken += l2_time
            energy_consumed += l2_energy
            if hit:
                self.l2_hits += 1
            else:
                self.l2_misses += 1
                hit, dram_time, dram_energy = self.dram.access(address, mode)
                time_taken += dram_time
                energy_consumed += dram_energy
                if not hit:
                    self.dram_accesses += 1

        self.time_ns += time_taken
        return hit, time_taken, energy_consumed
    
    def simulate(self, trace_file_path):
        self.time_ns = 0
        self.l1_instruction_hits = 0
        self.l1_instruction_misses = 0
        self.l1_data_hits = 0
        self.l1_data_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.dram_accesses = 0
        if trace_file_path.endswith('.Z'):
            with subprocess.Popen(['gunzip', '-c', trace_file_path], stdout=subprocess.PIPE) as proc:
                file = proc.stdout
        else:
            file = open(trace_file_path, 'r')
        with file:
            for line in file:
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                parts = line.strip().split()
                if len(parts) < 2:
                    continue 
                try:
                    operation_code = int(parts[0])
                    address = int(parts[1], 16)
                except ValueError:
                    continue
                if operation_code == 0:  # Memory read
                    self.access_memory(address, 'read')
                elif operation_code == 1:  # Memory write
                    self.access_memory(address, 'write')
                elif operation_code == 2:  # Instruction fetch
                    self.access_memory(address, 'read', is_instruction=True)
                elif operation_code == 3:  # Ignore
                    continue  
                elif operation_code == 4:  # Flush the cache
                    self.l1_data_cache.flush()
                    self.l1_instruction_cache.flush()
                    self.l2_cache.flush()

        if not trace_file_path.endswith('.Z'):
            file.close()

        self.calculate_idle_energy()
        self.calculate_performance_metrics()


class CacheLine:
    def __init__(self):
        self.valid = False
        self.tag = None
        self.data = [None] * 64

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
        index = (address // self.line_size) % self.num_lines
        tag = address // (self.line_size * self.num_lines)
        line = self.lines[index]
        energy_per_access_pj = (self.active_power * (self.access_time * 1e-9)) * 1e12
        self.energy_consumed += energy_per_access_pj

        if line.valid and line.tag == tag:
            if mode == 'write':
                line.dirty = True
            return True, self.access_time, energy_per_access_pj
        else:
            if line.valid and line.dirty:
                self.write_back(line)
            line.valid = True
            line.dirty = (mode == 'write')
            line.tag = tag
            return False, self.access_time, energy_per_access_pj
    
    def write_back(self, line):
        self.energy_consumed += (self.active_power * (self.access_time * 1e-9)) * 1e12

    def flush(self):
        for line in self.lines:
            if line.valid and line.dirty:
                self.write_back(line)
            line.valid = False
            line.dirty = False

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
        hit = False
        energy_per_access_pj = (self.active_power * (self.access_time * 1e-9)) * 1e12

        for line in cache_set:
            if line.valid and line.tag == tag:
                hit = True
                if mode == 'write':
                    line.dirty = True
                self.energy_consumed += energy_per_access_pj
                break

        if not hit:
            line_to_update = self.choose_line_to_evict(cache_set)
            if line_to_update.valid and line_to_update.dirty:
                self.write_back(line_to_update)
            line_to_update.valid = True
            line_to_update.dirty = (mode == 'write')
            line_to_update.tag = tag
            self.energy_consumed += energy_per_access_pj

        return hit, self.access_time, energy_per_access_pj

    def choose_line_to_evict(self, cache_set):
        return random.choice(cache_set)

    def write_back(self, line):
        self.energy_consumed += (self.active_power * (self.access_time * 1e-9)) * 1e12

    def flush(self):
        for cache_set in self.sets:
            for line in cache_set:
                if line.valid and line.dirty:
                    self.write_back(line)
                line.valid = False
                line.dirty = False

class DRAM:
    def __init__(self, size_gb, access_time, idle_power, active_power, transfer_penalty):
        self.size_gb = size_gb
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.transfer_penalty = transfer_penalty
        self.energy_consumed = 0 

    def access(self, address, mode):
        active_energy_pj = (self.active_power * (self.access_time * 1e-9)) * 1e12
        total_energy_pj = active_energy_pj + self.transfer_penalty
        self.energy_consumed += total_energy_pj
        return False, self.access_time, total_energy_pj

l1_instruction_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l1_data_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=4, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5)
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)

memory_system = MemorySubsystem(l1_instruction_cache, l1_data_cache, l2_cache, dram)

def run_simulation_on_all_traces(directory, memory_system):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if file_path.endswith('.din') or file_path.endswith('.Z'):
            print(f"Simulating file: {file_path}")
            memory_system.simulate(file_path)
            print(f"Finished simulating file: {file_path}\n")

directory_path = "C:\\Users\\foodrunner\\Desktop\\energyshit\\project1-eec-1\\Traces\\Spec_Benchmark"
run_simulation_on_all_traces(directory_path, memory_system)



def run_simulation_on_all_traces_AL(directory, base_l1_instruction_cache, base_l1_data_cache, base_dram):
    associativity_levels = [2, 4, 8]
    for assoc in associativity_levels:
        print(f"Running simulations with L2 cache associativity level: {assoc}")
        l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=assoc, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5)
        memory_system = MemorySubsystem(base_l1_instruction_cache, base_l1_data_cache, l2_cache, base_dram)
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if file_path.endswith('.din') or file_path.endswith('.Z'):
                print(f"Simulating file: {file_path}")
                memory_system.simulate(file_path)
                print(f"Finished simulating file: {file_path}\n")

directory_path = "C:\\Users\\foodrunner\\Desktop\\energyshit\\project1-eec-1\\Traces\\Spec_Benchmark"
l1_instruction_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l1_data_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)

run_simulation_on_all_traces_AL(directory_path, l1_instruction_cache, l1_data_cache, dram)

