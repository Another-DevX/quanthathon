"""Compara error de Trotter y error de Trotter + ruido desde CSV existentes."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
IDEAL_CSV = BASE_DIR / "trotter_convergence_h2_1le.csv"
NOISY_CSV = BASE_DIR / "trotter_convergence_h2_emulator.csv"
FIGURE_PATH = BASE_DIR / "trotter_noise_comparison.png"
SUMMARY_PATH = BASE_DIR / "trotter_noise_comparison_summary.csv"

KEY_COLUMNS = ["h_over_J", "time", "trotter_steps", "dt"]
OBSERVABLES = {
    "mz": r"$M_z$",
    "mz2": r"$M_z^2$",
    "czz": r"$C_{ZZ}$",
}
CONFIDENCE_Z = 1.96


def load_paired_results() -> pd.DataFrame:
    """Carga y valida los dos barridos sin ejecutar simulaciones."""
    ideal = pd.read_csv(IDEAL_CSV)
    noisy = pd.read_csv(NOISY_CSV)

    required_columns = set(KEY_COLUMNS)
    for observable in OBSERVABLES:
        required_columns.update(
            {
                f"sim_{observable}",
                f"exact_{observable}",
                f"abs_error_{observable}",
                f"se_{observable}",
            }
        )

    for name, dataframe in (("sin ruido", ideal), ("con ruido", noisy)):
        missing = required_columns.difference(dataframe.columns)
        if missing:
            raise ValueError(
                f"El CSV {name} no contiene las columnas: {sorted(missing)}"
            )
        if dataframe.duplicated(KEY_COLUMNS).any():
            raise ValueError(f"El CSV {name} contiene claves duplicadas.")

    paired = ideal.merge(
        noisy,
        on=KEY_COLUMNS,
        how="outer",
        suffixes=("_ideal", "_noisy"),
        validate="one_to_one",
        indicator=True,
    )
    if not paired["_merge"].eq("both").all():
        raise ValueError("Los barridos ideal y ruidoso no están emparejados.")
    paired = paired.drop(columns="_merge")

    for observable in OBSERVABLES:
        if not np.allclose(
            paired[f"exact_{observable}_ideal"],
            paired[f"exact_{observable}_noisy"],
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                f"Las referencias ED de {observable} no coinciden."
            )

        paired[f"noise_shift_{observable}"] = (
            paired[f"sim_{observable}_noisy"]
            - paired[f"sim_{observable}_ideal"]
        )
        paired[f"abs_noise_shift_{observable}"] = paired[
            f"noise_shift_{observable}"
        ].abs()
        paired[f"combined_se_{observable}"] = np.hypot(
            paired[f"se_{observable}_ideal"],
            paired[f"se_{observable}_noisy"],
        )
        paired[f"significant_noise_{observable}"] = (
            paired[f"abs_noise_shift_{observable}"]
            > CONFIDENCE_Z * paired[f"combined_se_{observable}"]
        )

    return paired.sort_values(KEY_COLUMNS).reset_index(drop=True)


def summarize_by_step(paired: pd.DataFrame) -> pd.DataFrame:
    """Resume las nueve combinaciones de campo y tiempo para cada paso."""
    rows = []
    for observable in OBSERVABLES:
        for steps, step_data in paired.groupby("trotter_steps", sort=True):
            ideal_error = step_data[f"abs_error_{observable}_ideal"]
            noisy_error = step_data[f"abs_error_{observable}_noisy"]
            absolute_shift = step_data[f"abs_noise_shift_{observable}"]
            signed_shift = step_data[f"noise_shift_{observable}"]
            combined_se = step_data[f"combined_se_{observable}"]
            sample_count = len(step_data)

            rows.append(
                {
                    "observable": observable,
                    "trotter_steps": int(steps),
                    "sample_count": sample_count,
                    "ideal_error_mean": ideal_error.mean(),
                    "ideal_error_q25": ideal_error.quantile(0.25),
                    "ideal_error_q75": ideal_error.quantile(0.75),
                    "noisy_error_mean": noisy_error.mean(),
                    "noisy_error_q25": noisy_error.quantile(0.25),
                    "noisy_error_q75": noisy_error.quantile(0.75),
                    "abs_noise_shift_mean": absolute_shift.mean(),
                    "abs_noise_shift_q25": absolute_shift.quantile(0.25),
                    "abs_noise_shift_q75": absolute_shift.quantile(0.75),
                    "signed_noise_shift_mean": signed_shift.mean(),
                    "signed_noise_shift_q25": signed_shift.quantile(0.25),
                    "signed_noise_shift_q75": signed_shift.quantile(0.75),
                    "mean_noise_resolution_95": (
                        CONFIDENCE_Z * combined_se.mean()
                    ),
                    "signed_mean_ci95": (
                        CONFIDENCE_Z
                        * np.sqrt(np.square(combined_se).sum())
                        / sample_count
                    ),
                    "significant_noise_points": int(
                        step_data[
                            f"significant_noise_{observable}"
                        ].sum()
                    ),
                }
            )

    return pd.DataFrame(rows)


def plot_comparison(summary: pd.DataFrame):
    """Genera la comparación agregada de los tres errores absolutos."""
    figure, axes = plt.subplots(
        len(OBSERVABLES),
        1,
        figsize=(10, 13),
    )
    colors = {
        "ideal": "#277DA1",
        "noisy": "#D1495B",
        "noise": "#7B2CBF",
        "resolution": "#555555",
    }

    for row, (observable, label) in enumerate(OBSERVABLES.items()):
        data = summary[
            summary["observable"].eq(observable)
        ].sort_values("trotter_steps")
        steps = data["trotter_steps"].to_numpy(dtype=float)
        absolute_axis = axes[row]

        absolute_series = [
            (
                "ideal_error",
                "Trotter sin ruido vs ED",
                colors["ideal"],
                "o",
            ),
            (
                "noisy_error",
                "Trotter + ruido vs ED",
                colors["noisy"],
                "s",
            ),
            (
                "abs_noise_shift",
                r"Efecto del ruido $|O_r-O_i|$",
                colors["noise"],
                "^",
            ),
        ]
        for prefix, legend, color, marker in absolute_series:
            mean = data[f"{prefix}_mean"].to_numpy(dtype=float)
            q25 = data[f"{prefix}_q25"].to_numpy(dtype=float)
            q75 = data[f"{prefix}_q75"].to_numpy(dtype=float)
            absolute_axis.loglog(
                steps,
                mean,
                color=color,
                marker=marker,
                linewidth=2,
                markersize=5,
                label=legend,
            )
            absolute_axis.fill_between(
                steps,
                np.maximum(q25, np.finfo(float).tiny),
                np.maximum(q75, np.finfo(float).tiny),
                color=color,
                alpha=0.12,
            )

        absolute_axis.loglog(
            steps,
            data["mean_noise_resolution_95"],
            color=colors["resolution"],
            linestyle=":",
            linewidth=1.5,
            label="Umbral detectable (95 %)",
        )

        noisy_optimum_index = data["noisy_error_mean"].idxmin()
        noisy_optimum = data.loc[noisy_optimum_index]
        absolute_axis.scatter(
            noisy_optimum["trotter_steps"],
            noisy_optimum["noisy_error_mean"],
            marker="*",
            s=180,
            color="#F4A261",
            edgecolor="black",
            linewidth=0.7,
            zorder=6,
            label=(
                "Mínimo ruidoso agregado"
                if row == 0
                else None
            ),
        )
        absolute_axis.annotate(
            f"óptimo: {int(noisy_optimum['trotter_steps'])}",
            (
                noisy_optimum["trotter_steps"],
                noisy_optimum["noisy_error_mean"],
            ),
            xytext=(7, 8),
            textcoords="offset points",
            fontsize=9,
        )

        absolute_axis.set_ylabel(f"Error medio en {label}")
        absolute_axis.grid(True, which="both", alpha=0.25)
        if row == 0:
            absolute_axis.set_title(
                "Error absoluto y efecto incremental del ruido"
            )
        if row == len(OBSERVABLES) - 1:
            absolute_axis.set_xlabel("Pasos de Trotter")

    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=3,
        frameon=False,
    )
    figure.suptitle(
        "TFIM N=8: Trotter ideal frente a Trotter con ruido\n"
        "Media sobre 3 valores de h/J × 3 tiempos; "
        "bandas = rango intercuartílico",
        fontsize=15,
        y=0.985,
    )
    figure.subplots_adjust(
        left=0.1,
        right=0.97,
        bottom=0.06,
        top=0.86,
        hspace=0.28,
    )
    return figure, axes


def print_conclusions(paired: pd.DataFrame, summary: pd.DataFrame) -> None:
    print(
        f"Comparación construida desde {len(paired)} pares de filas "
        f"({paired['trotter_steps'].nunique()} números de pasos)."
    )
    for observable, label in OBSERVABLES.items():
        data = summary[summary["observable"].eq(observable)]
        optimum = data.loc[data["noisy_error_mean"].idxmin()]
        crossover = data[
            data["abs_noise_shift_mean"] > data["ideal_error_mean"]
        ].iloc[0]
        significant = int(
            paired[f"significant_noise_{observable}"].sum()
        )
        print(
            f"{label}: mínimo ruidoso agregado en "
            f"{int(optimum['trotter_steps'])} pasos "
            f"(error medio={optimum['noisy_error_mean']:.4g}); "
            f"el ruido supera al error ideal desde "
            f"{int(crossover['trotter_steps'])} pasos; "
            f"{significant}/{len(paired)} diferencias son "
            "significativas al 95 %."
        )


def main() -> None:
    paired = load_paired_results()
    summary = summarize_by_step(paired)
    summary.to_csv(SUMMARY_PATH, index=False)
    figure, _ = plot_comparison(summary)
    figure.savefig(FIGURE_PATH, dpi=220, bbox_inches="tight")
    print_conclusions(paired, summary)
    print(f"Figura guardada en: {FIGURE_PATH}")
    print(f"Resumen guardado en: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
