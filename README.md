# Quanthathon — TFIM Digital Simulation on Quantinuum H2

Quantum simulation of the **Transverse-Field Ising Model (TFIM)** using first-order Suzuki-Trotter decomposition, executed on the Quantinuum H2-1LE emulator via QNexus.

## What it does

1. **Trotter circuit construction** — builds the time-evolution operator $e^{-iHt}$ as a quantum circuit using $R_x$ and $ZZ$ two-qubit gates.
2. **H2-1LE dynamics** — sweeps over $h/J \in \{0.5, 0.9, 1.0, 1.1, 2.0\}$ and $t \in [0, 1]$ on 8 qubits with 10 000 shots per circuit.
3. **Exact Diagonalization (ED) benchmark** — compares circuit results against analytically exact time evolution for observables $\langle M_z \rangle$, $\langle M_z^2 \rangle$, and $\langle C_{ZZ} \rangle$.
4. **Trotter convergence study** — measures error vs. number of Trotter steps at fixed $h/J = 1$, $t = 1, 2.5, 5$ using AerState statevector simulation and H2-1LE.
5. **Circuit cost analysis** — quantifies the gate count / depth trade-off as a function of Trotter steps compiled for H2-1LE.
6. **VQE ground state** — variational ansatz to find the TFIM ground state energy for each $h/J$ value.

## Dependencies

- [`qnexus`](https://docs.quantinuum.com/nexus/) — Quantinuum cloud job submission and result retrieval
- `pytket` + `pytket-quantinuum` — circuit construction and compilation
- `numpy`, `scipy`, `pandas`, `matplotlib`, `tqdm`

## Usage

Open `main.ipynb` and run cells sequentially. Jobs are cached under `qnexus_runs/` so re-running a section resumes from the saved job reference without resubmitting.

Pre-computed results are available as CSV files:

| File | Contents |
|------|----------|
| `h2_dynamics_observables.csv` | H2-1LE observable means and errors over time |
| `trotter_convergence_results.csv` | Convergence error vs. Trotter steps (AerState) |
| `trotter_compiled_cost_vs_error.csv` | Gate count / depth vs. Trotter steps (H2-1LE compiled) |

## Model

The Hamiltonian is the open-boundary TFIM:

$$H = -J \sum_{i} Z_i Z_{i+1} - h \sum_{i} X_i$$

Starting state: $|\psi(0)\rangle = |00\cdots0\rangle$.
