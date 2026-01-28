
# WoodLight Simulator Datapack Generator

To run simulations, put structure files in the `\designs` folder, run `generate_datapack.py`, put the generated datapack into a new void superflat world in a `1.16.1` instance(other versions are not tested), run `/function woodlight:setup` then `/function woodlight:start_{your design name}`.
To get analyzed data, run `process_logs.py` for the latest log(it updates the database incrementally so you only run it once for every simulation), then run `plotter.py` to see the smoothed PDF plotted and other data.
