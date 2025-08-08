# Benchmark

We can run simulation to compare the performance of native c executable file `cachesim`, and the python binding via [simulation.py](./simulation.py).

## Example

```bash
# at the root dir of the repository
bash script/install.sh
python benchmark/simulation.py  --trace_path=./src/libCacheSim/data/cloudPhysicsIO.oracleGeneral.bin
```

## Usage

```
python benchmark/simulation.py  -h
```