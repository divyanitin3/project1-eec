import random
import subprocess
import os

class MemorySubsystem:
    def __init__(self, l1_instruction_cache, l1_data_cache, l2_cache, dram, assoc_level,existing_metrics=None):
        self.l1_instruction_cache = l1_instruction_cache
        self.l1_data_cache = l1_data_cache
        self.l2_cache = l2_cache
        self.dram = dram
        self.assoc_level = assoc_level  # correctly initialize the associativity level
        self.reset_metrics()
        self.file_metrics = {}
        if existing_metrics is not None:
            self.file_metrics = existing_metrics
        else:
            self.file_metrics = {}


    def reset_metrics(self):
        self.time_ns = 0
        self.total_time_ns = 0
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
            'l2': {},  # Ensure this is a dictionary
            'dram': 0
        }
        # Ensure 'l2' is a dictionary and ready for a nested dictionary assignment
        if 'l2' not in self.energy_consumed or not isinstance(self.energy_consumed['l2'], dict):
            self.energy_consumed['l2'] = {}  # Initialize or reset if not a dictionary
        # Initialize the dictionary for the current associativity level within 'l2'
        self.energy_consumed['l2'][self.assoc_level] = {'hits': 0, 'misses': 0, 'energy': 0}

    def calculate_total_energy_and_time(self):
        # Calculate total energy and total time across all caches
        total_energy = self.l1_instruction_cache.energy_consumed + \
                       self.l1_data_cache.energy_consumed + \
                       sum(v['energy'] for v in self.energy_consumed['l2'].values()) + \
                       self.dram.energy_consumed

        total_time = self.time_ns  # Total time in nanoseconds

        return total_energy, total_time


    def store_file_metrics(self, filename):
        # Check if the file entry exists in the metrics dictionary
        if filename not in self.file_metrics:
            # Initialize all metrics for this file
            self.file_metrics[filename] = {
                'total_time_ns': self.time_ns,  # Initialize and set total_time_ns
                'l1_instruction': {'hits': self.l1_instruction_hits, 'misses': self.l1_instruction_misses, 'energy': self.l1_instruction_cache.energy_consumed},
                'l1_data': {'hits': self.l1_data_hits, 'misses': self.l1_data_misses, 'energy': self.l1_data_cache.energy_consumed},
                'l2': {self.assoc_level: {'hits': 0, 'misses': 0, 'energy': 0}},  # Initialize L2 for the current assoc_level
                'dram': {'accesses': self.dram_accesses, 'energy': self.dram.energy_consumed}
            }
        else:
            # File entry exists, update the total time
            

            self.file_metrics[filename]['total_time_ns'] += self.time_ns

            # Update existing metrics
            self.file_metrics[filename]['l1_instruction']['hits'] += self.l1_instruction_hits
            self.file_metrics[filename]['l1_instruction']['misses'] += self.l1_instruction_misses
            self.file_metrics[filename]['l1_instruction']['energy'] += self.l1_instruction_cache.energy_consumed
            self.file_metrics[filename]['l1_data']['hits'] += self.l1_data_hits
            self.file_metrics[filename]['l1_data']['misses'] += self.l1_data_misses
            self.file_metrics[filename]['l1_data']['energy'] += self.l1_data_cache.energy_consumed

            # Check and update L2 cache metrics for the current associativity level
            if self.assoc_level not in self.file_metrics[filename]['l2']:
                self.file_metrics[filename]['l2'][self.assoc_level] = {'hits': 0, 'misses': 0, 'energy': 0}

            self.file_metrics[filename]['l2'][self.assoc_level]['hits'] += self.l2_hits
            self.file_metrics[filename]['l2'][self.assoc_level]['misses'] += self.l2_misses
            self.file_metrics[filename]['l2'][self.assoc_level]['energy'] += self.l2_cache.energy_consumed

            self.file_metrics[filename]['dram']['accesses'] += self.dram_accesses
            self.file_metrics[filename]['dram']['energy'] += self.dram.energy_consumed




    def print_section_summary(self, section):
        print(f"\n{section.upper()} Cache Summary:")
        for filename, metrics in self.file_metrics.items():
            total_time_ns = metrics.get('total_time_ns', 0)
            if section in metrics:
                data = metrics[section]
                if section == 'dram':  # DRAM section
                    print(f"File: {filename} - Accesses: {data['accesses']}, Energy (pJ): {data['energy']}, Total Time (ns): {total_time_ns}")
                else:  # Other caches
                    print(f"File: {filename} - Hits: {data['hits']}, Misses: {data['misses']}, Energy (pJ): {data['energy']}, Total Time (ns): {metrics.get('total_time_ns', 0)}")
        
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
        self.time_ns += time_taken  # Make sure time is added here

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
                    self.time_ns += dram_time  # Add DRAM access time
                    self.dram_accesses += 1

        self.time_ns += time_taken
        return hit, time_taken, energy_consumed
    
    def simulate(self, trace_file_path):
        self.reset_metrics()
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

        time_taken = self.access_time

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
        time_taken = self.access_time  # Time is taken whether hit or miss
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
        time_taken = self.access_time  # Time taken on each DRAM access
        self.energy_consumed += total_energy_pj
        return False, self.access_time, total_energy_pj

l1_instruction_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
l1_data_cache = DirectMappedCache(size_kb=32, line_size=64, access_time=0.5, idle_power=0.5, active_power=1)
dram = DRAM(size_gb=8, access_time=50, idle_power=0.8, active_power=4, transfer_penalty=640)
l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=4, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5, next_level_cache=dram)
directory_path = "Traces/Spec_Benchmark"

def run_simulation_on_all_traces_AL(directory, base_l1_instruction_cache, base_l1_data_cache, base_dram):
    associativity_levels = [2, 4, 8]
    l2_summary = {}  # Dictionary to store L2 results by associativity level
    file_metrics = {}  

    # Create a dummy minimal L2 cache setup for general simulation that does not impact the results
    dummy_l2_cache = SetAssociativeCache(size_kb=1, line_size=64, assoc=4, access_time=1, idle_power=0, active_power=0, transfer_penalty=0, next_level_cache=None)
    general_memory_system = MemorySubsystem(base_l1_instruction_cache, base_l1_data_cache, dummy_l2_cache, base_dram,4,existing_metrics=file_metrics)

    # Process files for general L1 and DRAM stats
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if file_path.endswith('.din') or file_path.endswith('.Z'):
            print(f"Simulating for L1/DRAM general stats: {file_path}")
            general_memory_system.simulate(file_path)
            general_memory_system.store_file_metrics(filename)
            
    # Simulate with each L2 associativity
    for assoc in associativity_levels:
        print(f"\nPreparing simulations for L2 cache associativity level: {assoc}")
        l2_cache = SetAssociativeCache(size_kb=256, line_size=64, assoc=assoc, access_time=5, idle_power=0.8, active_power=2, transfer_penalty=5, next_level_cache=base_dram)
        memory_system = MemorySubsystem(base_l1_instruction_cache, base_l1_data_cache, l2_cache, base_dram,assoc,existing_metrics=file_metrics)
        l2_summary[assoc] = {}

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if file_path.endswith('.din') or file_path.endswith('.Z'):
                print(f"Simulating file: {file_path} with L2 associativity {assoc}")
                memory_system.simulate(file_path)
                if filename not in memory_system.file_metrics:
                    memory_system.file_metrics[filename] = {}
                memory_system.store_file_metrics(filename)

            l2_summary[assoc][filename] = memory_system.file_metrics.get(filename, {})

    general_memory_system.print_section_summary('l1_instruction')
    general_memory_system.print_section_summary('l1_data')
    general_memory_system.print_section_summary('dram')


    # Print L2 summaries per associativity level
    for assoc, files in l2_summary.items():
        print(f"L2 CACHE Summary by Associativity Level {assoc}:")
        for filename, metrics in files.items():
            l2_data = metrics.get('l2', {}).get(assoc, {})
            print(f"File: {filename} - Hits: {l2_data.get('hits', [])}, Misses: {l2_data.get('misses', [])}, Energy (pJ): {l2_data.get('energy', 0)}, Total Time (ns): {metrics.get('total_time_ns',0)}")
        
    total_energy, total_time = general_memory_system.calculate_total_energy_and_time()
    print(f"\nTotal Energy Consumed across all components (pJ): {total_energy}")
    print(f"Total Simulation Time across all components (ns): {total_time}")

run_simulation_on_all_traces_AL(directory_path, l1_instruction_cache, l1_data_cache, dram)

