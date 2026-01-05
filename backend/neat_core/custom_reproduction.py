"""
Custom Reproduction

NEAT-Pythonの親候補最低2個体の制約を1に変更
"""

import math
import random
from itertools import count

from neat.reproduction import DefaultReproduction
from neat.math_util import mean
from neat.six_util import iteritems, itervalues


class CustomReproduction(DefaultReproduction):
    """
    DefaultReproductionを継承し、親候補の最低数を1に変更
    """

    def reproduce(self, config, species, pop_size, generation):
        all_fitnesses = []
        remaining_species = []
        for stag_sid, stag_s, stagnant in self.stagnation.update(species, generation):
            if stagnant:
                self.reporters.species_stagnant(stag_sid, stag_s)
            else:
                all_fitnesses.extend(m.fitness for m in itervalues(stag_s.members))
                remaining_species.append(stag_s)

        if not remaining_species:
            species.species = {}
            return {}

        min_fitness = min(all_fitnesses)
        max_fitness = max(all_fitnesses)
        fitness_range = max(1.0, max_fitness - min_fitness)
        for afs in remaining_species:
            msf = mean([m.fitness for m in itervalues(afs.members)])
            af = (msf - min_fitness) / fitness_range
            afs.adjusted_fitness = af

        adjusted_fitnesses = [s.adjusted_fitness for s in remaining_species]
        avg_adjusted_fitness = mean(adjusted_fitnesses)
        self.reporters.info("Average adjusted fitness: {:.3f}".format(avg_adjusted_fitness))

        previous_sizes = [len(s.members) for s in remaining_species]
        min_species_size = self.reproduction_config.min_species_size
        min_species_size = max(min_species_size, self.reproduction_config.elitism)
        spawn_amounts = self.compute_spawn(adjusted_fitnesses, previous_sizes,
                                           pop_size, min_species_size)

        new_population = {}
        species.species = {}
        for spawn, s in zip(spawn_amounts, remaining_species):
            spawn = max(spawn, self.reproduction_config.elitism)
            assert spawn > 0

            old_members = list(iteritems(s.members))
            s.members = {}
            species.species[s.key] = s

            old_members.sort(reverse=True, key=lambda x: x[1].fitness)

            if self.reproduction_config.elitism > 0:
                for i, m in old_members[:self.reproduction_config.elitism]:
                    new_population[i] = m
                    spawn -= 1

            if spawn <= 0:
                continue

            repro_cutoff = int(math.ceil(self.reproduction_config.survival_threshold *
                                         len(old_members)))
            # 変更点: 最低2→1に変更
            repro_cutoff = max(repro_cutoff, 1)
            old_members = old_members[:repro_cutoff]

            while spawn > 0:
                spawn -= 1
                parent1_id, parent1 = random.choice(old_members)
                parent2_id, parent2 = random.choice(old_members)
                gid = next(self.genome_indexer)
                child = config.genome_type(gid)
                child.configure_crossover(parent1, parent2, config.genome_config)
                child.mutate(config.genome_config)
                new_population[gid] = child
                self.ancestors[gid] = (parent1_id, parent2_id)

        return new_population
