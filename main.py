import random
import subprocess
import os
import statistics

class MemorySubsystem:
    def __init__(self, l1_instruction_cache, l1_data_cache, l2_cache, dram):
        self.l1_instruction_cache = l1_instruction_cache
        self.l1_data_cache = l1_data_cache
        self.l2_cache = l2_cache
        self.dram = dram
        self.reset_metrics()

    def reset_metrics(self):
        self.time_ns = 0
        self.l1_instruction_hits = 0
        self.l1_instruction_misses = 0
        self.l1_data_hits = 0
        self.l1_data_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0
        self.dram_accesses = 0
        self.energy_consumed = {
            'l1_instruction': 0,
            'l1_data': 0,
            'l2': 0,
            'dram': 0
        }

    def print_summary(self):
        print("L1 Instruction Cache Summary:")
        self.print_cache_summary('l1_instruction')
        print("L1 Data Cache Summary:")
        self.print_cache_summary('l1_data')
        print("L2 Cache Summary:")
        self.print_cache_summary('l2')
        print("DRAM Summary:")
        self.print_dram_summary()

    def print_cache_summary(self, level):
        total_hits = getattr(self, f"{level}_hits")
        total_misses = getattr(self, f"{level}_misses")
        total_accesses = total_hits + total_misses
        miss_rate = total_misses / total_accesses if total_accesses else 0
        print(f"Avg Misses: {total_misses}")
        print(f"Avg Hits: {total_hits}")
        print(f"Avg Total Accesses: {total_accesses}")
        print(f"Avg Miss Rate: {miss_rate * 100:.2f}%")
        print(f"Avg Total Energy (nJ): {self.energy_consumed[level]}")
        print(f"Total Time (ns): {self.time_ns}")

    def print_dram_summary(self):
        print(f"Avg Accesses: {self.dram_accesses}")
        print(f"Avg Total Energy (nJ): {self.energy_consumed['dram']}")
        
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

        miss_rate = total_misses / total_accesses if total_accesses else 0

        print(f"Total Hits: {total_hits}")
        print(f"Total Misses: {total_misses}")
        print(f"L1 Instruction Cache Hits: {self.l1_instruction_hits}, Misses: {self.l1_instruction_misses}")
        print(f"L1 Data Cache Hits: {self.l1_data_hits}, Misses: {self.l1_data_misses}")
        print(f"L2 Cache Hits: {self.l2_hits}, Misses: {self.l2_misses}")
        print(f"DRAM Accesses: {self.dram_accesses}")
        print(f"Total Energy Consumed (pJ): {total_energy}")
        print(f"Average Access Time (ns): {average_access_time_ns}")
        print(f"Miss Rate (%): {miss_rate * 100}")

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
                elif operation_code == 4:  # Flush Ignore
                    continue

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
    def __init__(self, size_kb, line_size, access_time, idle_power, active_power, next_level_cache=None):
        self.size_kb = size_kb
        self.line_size = line_size
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.next_level_cache = next_level_cache  # Optional next-level cache for write-back
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
        if self.next_level_cache:
            # Simulate asynchronous write-back to next level cache
            address = line.tag * (self.line_size * self.num_lines)  # Reconstruct the address from the tag
            _, _, energy = self.next_level_cache.access(address, 'write', is_instruction=False)
            self.energy_consumed += energy

class SetAssociativeCache:
    def __init__(self, size_kb, line_size, assoc, access_time, idle_power, active_power, transfer_penalty, next_level_cache=None):
        self.size_kb = size_kb
        self.line_size = line_size
        self.assoc = assoc
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.transfer_penalty = transfer_penalty
        self.next_level_cache = next_level_cache
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
        if self.next_level_cache:
            address = line.tag * (self.line_size * len(self.sets))  # Calculate the global address
            _, _, energy = self.next_level_cache.access(address, 'write')
            self.energy_consumed

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
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)
l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=4, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5, next_level_cache=dram)
memory_system = MemorySubsystem(l1_instruction_cache, l1_data_cache, l2_cache, dram)
directory_path = "C:\\Users\\foodrunner\\Desktop\\energyshit\\project1-eec-1\\Traces\\Spec_Benchmark"

def run_simulation_on_all_traces_AL(directory, base_l1_instruction_cache, base_l1_data_cache, base_dram):
    associativity_levels = [2, 4, 8]
    for assoc in associativity_levels:
        print(f"Running simulations with L2 cache associativity level: {assoc}")
        l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=assoc, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5, next_level_cache=dram)
        memory_system = MemorySubsystem(base_l1_instruction_cache, base_l1_data_cache, l2_cache, base_dram)
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if file_path.endswith('.din') or file_path.endswith('.Z'):
                print(f"Simulating file: {file_path}")
                memory_system.simulate(file_path)
                print(f"Finished simulating file: {file_path}\n")
        memory_system.print_summary()
                
run_simulation_on_all_traces_AL(directory_path, l1_instruction_cache, l1_data_cache, dram)
































'''

def run_simulation_multiple_times(directory, memory_system, num_runs=10):
    results = {}

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if file_path.endswith('.din') or file_path.endswith('.Z'):
            print(f"Starting simulation for: {file_path}")

            times = []
            energies = []
            l1_instruction_hits = []
            l1_instruction_misses = []
            l1_data_hits = []
            l1_data_misses = []
            l2_hits = []
            l2_misses = []
            dram_accesses = []

            for _ in range(num_runs):
                memory_system.simulate(file_path)

                times.append(memory_system.time_ns)
                energies.append(memory_system.l1_instruction_cache.energy_consumed +
                                memory_system.l1_data_cache.energy_consumed +
                                memory_system.l2_cache.energy_consumed +
                                memory_system.dram.energy_consumed)

                l1_instruction_hits.append(memory_system.l1_instruction_hits)
                l1_instruction_misses.append(memory_system.l1_instruction_misses)
                l1_data_hits.append(memory_system.l1_data_hits)
                l1_data_misses.append(memory_system.l1_data_misses)
                l2_hits.append(memory_system.l2_hits)
                l2_misses.append(memory_system.l2_misses)
                dram_accesses.append(memory_system.dram_accesses)

                memory_system.reset_metrics()

            avg_time = statistics.mean(times)
            std_dev_time = statistics.stdev(times)
            avg_energy = statistics.mean(energies)
            std_dev_energy = statistics.stdev(energies)

            results[filename] = {
                'average_time_ns': avg_time,
                'time_std_dev_ns': std_dev_time,
                'average_energy_pJ': avg_energy,
                'energy_std_dev_pJ': std_dev_energy
            }

            print(f"Finished simulations for: {file_path}")

    return results 
            
def reset_metrics(self):
    self.time_ns = 0
    self.l1_instruction_hits = 0
    self.l1_instruction_misses = 0
    self.l1_data_hits = 0
    self.l1_data_misses = 0
    self.l2_hits = 0
    self.l2_misses = 0
    self.dram_accesses = 0
    self.l1_instruction_cache.energy_consumed = 0
    self.l1_data_cache.energy_consumed = 0
    self.l2_cache.energy_consumed = 0
    self.dram.energy_consumed = 0

MemorySubsystem.reset_metrics = reset_metrics

results = run_simulation_multiple_times(directory_path, memory_system)

def print_results_table(results):
    print(f"{'Filename':<30} {'Avg Time (ns)':>15} {'Time Std Dev (ns)':>20} {'Avg Energy (pJ)':>20} {'Energy Std Dev (pJ)':>20}")
    print("-" * 105)
    for filename, metrics in results.items():
        print(f"{filename:<30} {metrics['average_time_ns']:>15.2f} {metrics['time_std_dev_ns']:>20.2f} {metrics['average_energy_pJ']:>20.2f} {metrics['energy_std_dev_pJ']:>20.2f}")

print_results_table(results)

'''
