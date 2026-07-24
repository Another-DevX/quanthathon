# Quanthathon — TFIM Digital Simulation on Quantinuum H2

Quantum simulation of the **Transverse-Field Ising Model (TFIM)** using first-order Suzuki-Trotter decomposition, executed on the Quantinuum H2-1LE emulator via QNexus.

## Notebooks

The repository deliberately contains two notebooks with slightly different
circuits. They are separate deliverables and must be reviewed one by one:

- `main.ipynb` — standard TFIM Trotter circuit, exact-diagonalization
  benchmarks, convergence, circuit cost, and VQE.
- `iceberg.ipynb` — Iceberg error-detection circuit, including syndrome and
  parity filtering.

Results and circuit assumptions from one notebook must not be treated as
interchangeable with those from the other.

## What it does

1. **Trotter circuit construction** — builds the time-evolution operator $e^{-iHt}$ as a quantum circuit using $R_x$ and $ZZ$ two-qubit gates.
2. **H2-1LE dynamics** — sweeps over $h/J \in \{0.5, 0.9, 1.0, 1.1, 2.0\}$ and $t \in [0, 1]$ on 8 qubits with 10 000 shots per circuit.
3. **Exact Diagonalization (ED) benchmark** — compares circuit results against analytically exact time evolution for observables $\langle M_z \rangle$, $\langle M_z^2 \rangle$, and $\langle C_{ZZ} \rangle$.
4. **Trotter convergence study** — measures error vs. number of Trotter steps at fixed $h/J = 1$, $t = 1, 2.5, 5$ using AerState statevector simulation and H2-1LE.
5. **Circuit cost analysis** — quantifies the gate count / depth trade-off as a function of Trotter steps compiled for H2-1LE.
6. **VQE ground state** — variational ansatz to find the TFIM ground state energy for each $h/J$ value.
7. **Finite-size VQE benchmark** — compares cached VQE measurements (with standard errors) against exact diagonalization of the same open $N=8$ chain for $\langle M_z^2\rangle$ and $\langle M_x\rangle$.

## Dependencies

- [`qnexus`](https://docs.quantinuum.com/nexus/) — Quantinuum cloud job submission and result retrieval
- `pytket` + `pytket-offline-display` — circuit construction and display
- `qiskit` + `pylatexenc` — circuit conversion and rendering in `iceberg.ipynb`
- `numpy`, `scipy`, `pandas`, `matplotlib`, `tqdm`

All direct Python dependencies are declared in `requirements.txt`. The first
cell of each notebook installs that file, so the notebooks and the standalone
environment use the same dependency list.

## Usage

Install the environment with:

```bash
python -m pip install -r requirements.txt
```

Then open either notebook from the repository root. Review and run
`main.ipynb` and `iceberg.ipynb` separately, in order, rather than mixing
cells between them. QNexus cells require credentials and may submit or recover
cloud jobs; reviewing the saved notebook outputs and published result files
does not.

Pre-computed results are available as CSV files:

| File | Contents |
|------|----------|
| `h2_1le_dynamics_observables.csv` | Standard-circuit H2-1LE observable means and errors over time |
| `h2_dynamics_observables.csv` | Iceberg filtered/unfiltered dynamics and exact reference values |
| `h2_qed_statistics.csv` | Iceberg syndrome/parity rejection statistics |
| `trotter_convergence_results.csv` | Ideal statevector convergence error vs. Trotter steps |
| `trotter_convergence_h2_1le.csv` | Shot-based H2-1LE convergence results |
| `trotter_convergence_h2_emulator.csv` | Shot-based noisy H2-Emulator convergence results |
| `trotter_compiled_cost_vs_error.csv` | Gate count / depth vs. Trotter steps (H2-1LE compiled) |
| `h2_emulator_trotter_cost_and_error_floor.csv` | Compiled cost and independent gate-fault exposure estimate |
| `tfim-vqe-hva-p4-n8-v2-results.csv` | VQE ground-state observables and uncertainties; reused automatically when the $h/J$ grid and ansatz depth match |
| `trotter_noise_comparison_summary.csv` | Aggregated ideal/noisy convergence comparison used by the published figure |

The VQE cell loads this CSV by default, so re-running the notebook does not
repeat the local optimization or submit another H2-1LE job. Set
`VQE_FORCE_RERUN = True` in that cell only when a fresh run is intended.

The ideal/noisy convergence figure can be regenerated without QNexus:

```bash
python plot_trotter_noise_comparison.py
```

The CSV files and saved notebook outputs are sufficient to review the reported
results without launching new jobs. The stable CSVs above also reproduce the
published convergence comparison and the Iceberg analyses.

One row-level dataset is not currently present: the standard-circuit noisy
time sweep (`resultados_con_ruido` in `main.ipynb`). Its saved plots can be
reviewed in the notebook, but regenerating those particular plots requires
exporting the original run's `dynamics_observables.csv` as a stable repository
file (it must not be replaced with the Iceberg CSV because the circuits differ).
A clean, end-to-end execution of every notebook cell likewise requires QNexus
access because the notebooks contain job-submission and result-recovery
sections.

## Model

The Hamiltonian is the open-boundary TFIM:

$$H = -J \sum_{i} Z_i Z_{i+1} - h \sum_{i} X_i$$

Starting state: $|\psi(0)\rangle = |00\cdots0\rangle$.
