"""Implements the core evolution algorithm."""
from __future__ import print_function

import os
import sys
import subprocess
from custom_neat_lib.reporting import ReporterSet
from custom_neat_lib.math_util import mean, oscillator
from custom_neat_lib.six_util import iteritems, itervalues
from custom_neat_lib._added import save_files_secure_backups, update_puzzles_diff


class CompleteExtinctionException(Exception):
    pass


class Population(object):
    """
    This class implements the core evolution algorithm:
        1. Evaluate fitness of all genomes.
        2. Check to see if the termination criterion is satisfied; exit if it is.
        3. Generate the next generation from the current population.
        4. Partition the new generation into species based on genetic similarity.
        5. Go to 1.
    """

    def __init__(self, config, initial_state=None, path_champions=None):
        self.reporters = ReporterSet()
        self.config = config
        self.path_champions = path_champions #   ADDED CHESS
        stagnation = config.stagnation_type(config.stagnation_config, self.reporters)
        self.reproduction = config.reproduction_type(config.reproduction_config,
                                                     self.reporters,
                                                     stagnation)
        if config.fitness_criterion == 'max':
            self.fitness_criterion = max
        elif config.fitness_criterion == 'min':
            self.fitness_criterion = min
        elif config.fitness_criterion == 'mean':
            self.fitness_criterion = mean
        elif not config.no_fitness_termination:
            raise RuntimeError(
                "Unexpected fitness_criterion: {0!r}".format(config.fitness_criterion))

        if initial_state is None:
            # Create a population from scratch, then partition into species.
            self.population = self.reproduction.create_new(config.genome_type,
                                                           config.genome_config,
                                                           config.pop_size)
            self.species = config.species_set_type(config.species_set_config, self.reporters)
            self.generation = 0
            self.species.speciate(config, self.population, self.generation)
        else:
            self.population, self.species, self.generation = initial_state
            if hasattr(self.species, 'reporters'):
                self.species.reporters = self.reporters

        self.best_genome = None

        # ----- chess advancements -----

        # prepare oscillators
        self.original_population_size = 200         # self.config.pop_size
        self.original_conn_add_prob = 0.15          # self.config.genome_config.conn_add_prob
        self.original_conn_delete_prob = 0.12        # self.config.genome_config.conn_delete_prob
        self.original_node_add_prob = 0.15          # self.config.genome_config.node_add_prob
        self.original_node_delete_prob = 0.12        # self.config.genome_config.node_delete_prob
        self.original_weight_mutate_power = 0.1    # self.config.genome_config.weight_mutate_power
        self.original_response_mutate_power = 0.1  # self.config.genome_config.response_mutate_power
        self.original_bias_mutate_power = 0.1      # self.config.genome_config.bias_mutate_power

        # ------------------------------



    def add_reporter(self, reporter):
        self.reporters.add(reporter)

    def remove_reporter(self, reporter):
        self.reporters.remove(reporter)

    def run(self, fitness_function, n=None, global_lock=None):
        """
        Runs NEAT's genetic algorithm for at most n generations.  If n
        is None, run until solution is found or extinction occurs.

        The user-provided fitness_function must take only two arguments:
            1. The population as a list of (genome id, genome) tuples.
            2. The current configuration object.

        The return value of the fitness function is ignored, but it must assign
        a Python float to the `fitness` member of each genome.

        The fitness function is free to maintain external state, perform
        evaluations in parallel, etc.

        It is assumed that fitness_function does not modify the list of genomes,
        the genomes themselves (apart from updating the fitness member),
        or the configuration object.
        """

        if self.config.no_fitness_termination and (n is None):
            raise RuntimeError("Cannot have no generational limit with no fitness termination")

        k = 0

        while n is None or k < n:
            k += 1

            self.reporters.start_generation(self.generation)

            # Evaluate all genomes using the user-provided function.
            fitness_function(list(iteritems(self.population)), self.config, self.path_champions, self.generation)

            # Gather and report statistics.
            best = None
            for g in itervalues(self.population):
                if best is None or g.fitness > best.fitness:
                    best = g
            self.reporters.post_evaluate(self.config, self.population, self.species, best)

            # Track the best genome ever seen.
            if self.best_genome is None or best.fitness > self.best_genome.fitness:
                self.best_genome = best

            if not self.config.no_fitness_termination:
                # End if the fitness threshold is reached.
                fv = self.fitness_criterion(g.fitness for g in itervalues(self.population))
                if fv >= self.config.fitness_threshold:
                    self.reporters.found_solution(self.config, self.generation, best)
                    break


            # -------- chess advancements --------

            # --- puzzle diff update ---
            update_puzzles_diff()

            # - custom puzzles -

            puzzle_generator_path = '__puzzle_generator_V2_PGN.py'
            puzzle_filter_path = '__puzzleV2_FILTER.py'
            if not os.path.isfile(puzzle_generator_path):
                root_gen = os.path.join(os.path.dirname(os.path.dirname(__file__)), '__puzzle_generator_V2_PGN.py')
                if os.path.isfile(root_gen):
                    puzzle_generator_path = os.path.relpath(root_gen)
            if not os.path.isfile(puzzle_filter_path):
                root_fil = os.path.join(os.path.dirname(os.path.dirname(__file__)), '__puzzleV2_FILTER.py')
                if os.path.isfile(root_fil):
                    puzzle_filter_path = os.path.relpath(root_fil)

            if self.generation%50 == 0 and self.generation > 0:
                from custom_neat_lib.puzzles_pgn_handler import merge_pgns
                merge_pgns("nn")

                # run puzzle generator
                subprocess.run([sys.executable, puzzle_generator_path])

                # run puzzle filter
                #subprocess.run([sys.executable, puzzle_filter_path])


            AMOUNT_SPECIES_WANTED = 7.0
            INCREMENT = 0.03
            ROUND_POINTS = 3

            number_of_species = len(self.species.species)
            diff = min(number_of_species - AMOUNT_SPECIES_WANTED, 3)

            old_compatibility_threshold = self.config.species_set_config.compatibility_threshold
            self.config.species_set_config.compatibility_threshold = \
                round(self.config.species_set_config.compatibility_threshold + ((diff-0.5) * INCREMENT), ROUND_POINTS)

            if old_compatibility_threshold < self.config.species_set_config.compatibility_threshold:
                direction_compatibility_threshold = "UP"
            elif old_compatibility_threshold == self.config.species_set_config.compatibility_threshold:
                direction_compatibility_threshold = "SAME"
            else:
                direction_compatibility_threshold = "DOWN"

            old_max_stagnation = self.config.stagnation_config.max_stagnation
            if self.generation%2 == 0 and diff < 0:
                self.config.stagnation_config.max_stagnation += 1
            elif self.generation%2 == 0 and diff > 0:
                self.config.stagnation_config.max_stagnation -= 1
            elif diff > 1:
                self.config.stagnation_config.max_stagnation -= 1

            self.config.stagnation_config.max_stagnation = max(int(self.config.stagnation_config.max_stagnation), 5)
            self.config.stagnation_config.max_stagnation = min(int(self.config.stagnation_config.max_stagnation), 200)

            if old_max_stagnation < self.config.stagnation_config.max_stagnation:
                direction_max_stagnation = "UP"
            elif old_max_stagnation == self.config.stagnation_config.max_stagnation:
                direction_max_stagnation = "SAME"
            else:
                direction_max_stagnation = "DOWN"

            # --- oscilate ---

            # nodes
            old_node_add_prob = self.config.genome_config.node_add_prob
            old_delete_prob = self.config.genome_config.node_delete_prob
            self.config.genome_config.node_add_prob = round(oscillator(self.original_node_add_prob, 40, self.generation), 5)
            self.config.genome_config.node_delete_prob = round(oscillator(self.original_node_delete_prob, 41, self.generation), 5)

            if self.config.genome_config.node_add_prob > old_node_add_prob:
                direction_node_add_prob = "UP"
            elif self.config.genome_config.node_add_prob == old_node_add_prob:
                direction_node_add_prob = "SAME"
            else:
                direction_node_add_prob = "DOWN"

            if self.config.genome_config.node_delete_prob > old_delete_prob:
                direction_node_delete_prob = "UP"
            elif self.config.genome_config.node_delete_prob == old_delete_prob:
                direction_node_delete_prob = "SAME"
            else:
                direction_node_delete_prob = "DOWN"

            # connections
            old_conn_add_prob = self.config.genome_config.conn_add_prob
            old_conn_delete_prob = self.config.genome_config.conn_delete_prob
            self.config.genome_config.conn_add_prob = round(oscillator(self.original_conn_add_prob, 42, self.generation), 5)
            self.config.genome_config.conn_delete_prob = round(oscillator(self.original_conn_delete_prob, 43, self.generation), 5)

            if self.config.genome_config.conn_add_prob > old_conn_add_prob:
                direction_conn_add_prob = "UP"
            elif self.config.genome_config.conn_add_prob == old_conn_add_prob:
                direction_conn_add_prob = "SAME"
            else:
                direction_conn_add_prob = "DOWN"

            if self.config.genome_config.conn_delete_prob > old_conn_delete_prob:
                direction_conn_delete_prob = "UP"
            elif self.config.genome_config.conn_delete_prob == old_conn_delete_prob:
                direction_conn_delete_prob = "SAME"
            else:
                direction_conn_delete_prob = "DOWN"

            # powers
            old_weight_mutate_power = self.config.genome_config.weight_mutate_power
            old_response_mutate_power = self.config.genome_config.response_mutate_power
            old_bias_mutate_power = self.config.genome_config.bias_mutate_power

            self.config.genome_config.weight_mutate_power = round(oscillator(self.original_weight_mutate_power, 44, self.generation), 5)
            self.config.genome_config.response_mutate_power = round(oscillator(self.original_response_mutate_power, 45, self.generation), 5)
            self.config.genome_config.bias_mutate_power = round(oscillator(self.original_bias_mutate_power, 46, self.generation), 5)

            if self.config.genome_config.weight_mutate_power > old_weight_mutate_power:
                direction_weight_mutate_power = "UP"
            elif self.config.genome_config.weight_mutate_power == old_weight_mutate_power:
                direction_weight_mutate_power = "SAME"
            else:
                direction_weight_mutate_power = "DOWN"

            if self.config.genome_config.response_mutate_power > old_response_mutate_power:
                direction_response_mutate_power = "UP"
            elif self.config.genome_config.response_mutate_power == old_response_mutate_power:
                direction_response_mutate_power = "SAME"
            else:
                direction_response_mutate_power = "DOWN"

            if self.config.genome_config.bias_mutate_power > old_bias_mutate_power:
                direction_bias_mutate_power = "UP"
            elif self.config.genome_config.bias_mutate_power == old_bias_mutate_power:
                direction_bias_mutate_power = "SAME"
            else:
                direction_bias_mutate_power = "DOWN"

            # population size
            old_pop_size = self.config.pop_size
            self.config.pop_size = round(0.3*oscillator(self.original_population_size, 50, self.generation)+0.7*self.original_population_size)
            if self.config.pop_size > old_pop_size:
                direction_pop_size = "UP"
            elif self.config.pop_size == old_pop_size:
                direction_pop_size = "SAME"
            else:
                direction_pop_size = "DOWN"

            #save_files_secure_backups()

            print("\nNew population size:", self.config.pop_size, str("(" + str(direction_pop_size) + ")"))
            print("New compatibility_threshold:", self.config.species_set_config.compatibility_threshold,
                  str("(" + str(direction_compatibility_threshold) + ")"))

            print("\nNew node_add_prob:", self.config.genome_config.node_add_prob, str("(" + str(direction_node_add_prob) + ")"))
            print("New node_delete_prob:", self.config.genome_config.node_delete_prob, str("(" + str(direction_node_delete_prob) + ")"))

            print("New conn_add_prob:", self.config.genome_config.conn_add_prob, str("(" + str(direction_conn_add_prob) + ")"))
            print("New conn_delete_prob:", self.config.genome_config.conn_delete_prob, str("(" + str(direction_conn_delete_prob) + ")"))

            print("New weight_mutate_power:", self.config.genome_config.weight_mutate_power, str("(" + str(direction_weight_mutate_power) + ")"))
            print("New response_mutate_power:", self.config.genome_config.response_mutate_power, str("(" + str(direction_response_mutate_power) + ")"))
            print("New bias_mutate_power:", self.config.genome_config.bias_mutate_power, str("(" + str(direction_bias_mutate_power) + ")"),"\n")

            print("New max stagnation:", self.config.stagnation_config.max_stagnation, str("(" + str(direction_max_stagnation) + ")"), "\n")

            # ----------------




            # ------------------------------


            # Create the next generation from the current generation.
            self.population = self.reproduction.reproduce(self.config, self.species,
                                                          self.config.pop_size, self.generation)

            # Check for complete extinction.
            if not self.species.species:
                self.reporters.complete_extinction()

                # If requested by the user, create a completely new population,
                # otherwise raise an exception.
                if self.config.reset_on_extinction:
                    self.population = self.reproduction.create_new(self.config.genome_type,
                                                                   self.config.genome_config,
                                                                   self.config.pop_size)
                else:
                    raise CompleteExtinctionException()

            # Divide the new population into species.
            self.species.speciate(self.config, self.population, self.generation)

            self.reporters.end_generation(self.config, self.population, self.species)

            self.generation += 1

        if self.config.no_fitness_termination:
            self.reporters.found_solution(self.config, self.generation, self.best_genome)

        return self.best_genome
