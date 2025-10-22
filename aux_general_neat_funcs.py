def restore_checkpoint(filename):
    import gzip
    import pickle
    import random
    from neat import Population
    """Resumes the simulation from a previous saved point."""
    with gzip.open(filename) as f:
        generation, config, population, species_set, rndstate = pickle.load(f)
        generation += 1  # making new generation
        random.setstate(rndstate)
        return Population(config, (population, species_set, generation))



