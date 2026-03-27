from io import BytesIO
from extensions import cache
import pandas as pd
import numpy as np
import os
from pathlib import Path
import joblib
from umap import UMAP
from topas_portal.constants import IntensityUnit

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import seaborn as sns

matplotlib.use("svg")


import db

cohorts_db = db.cohorts_db


PRODICT_PROB_CACHE_ID_TEMPLATE = "prodict_prob_{sample}_{ext}"
PRODICT_UMAP_CACHE_ID_TEMPLATE = (
    "prodict_umap_{sample}_{cohort}_{background_cohort}_{ext}"
)
TOPAS_RTK_CACHE_ID_TEMPLATE = "topas_rtk_{sample}_{cohort}_{background_cohort}_{ext}"
TOPAS_CK_CACHE_ID_TEMPLATE = "topas_ck_{sample}_{cohort}_{background_cohort}_{ext}"
TUMOR_ANTIGEN_CACHE_ID_TEMPLATE = (
    "tumor_antigens_{sample}_{cohort}_{background_cohort}_{ext}"
)
IMMUNE_HEATMAP_CACHE_ID_TEMPLATE = "immune_heatmap_{sample}_{cohort}_{ext}"


class PatientReport:
    def __init__(self, cohort_id: int, patient: str, background_cohort: str = None):
        self._patient = patient
        self._cohort_id = cohort_id
        self._background_cohort = background_cohort

    def get_prodict_prob_cache_id(self, ext):
        return PRODICT_PROB_CACHE_ID_TEMPLATE.format_map(
            {"sample": self._patient, "ext": ext}
        )

    def get_prodict_umap_cache_id(self, ext):
        return PRODICT_UMAP_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": self._patient,
                "cohort": self._cohort_id,
                "background_cohort": (
                    self._background_cohort if self._background_cohort else "default"
                ),
                "ext": ext,
            }
        )

    def get_topas_rtk_cache_id(self, ext):
        return TOPAS_RTK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": self._patient,
                "cohort": self._cohort_id,
                "background_cohort": (
                    self._background_cohort if self._background_cohort else "default"
                ),
                "ext": ext,
            }
        )

    def get_topas_ck_cache_id(self, ext):
        return TOPAS_CK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": self._patient,
                "cohort": self._cohort_id,
                "background_cohort": (
                    self._background_cohort if self._background_cohort else "default"
                ),
                "ext": ext,
            }
        )

    def get_antigens_cache_id(self, ext):
        return TUMOR_ANTIGEN_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": self._patient,
                "cohort": self._cohort_id,
                "background_cohort": (
                    self._background_cohort if self._background_cohort else "default"
                ),
                "ext": ext,
            }
        )

    def get_immune_heatmap_cache_id(self, ext):
        return IMMUNE_HEATMAP_CACHE_ID_TEMPLATE.format_map(
            {"sample": self._patient, "cohort": self._cohort_id, "ext": ext}
        )

    def setup_prodict_scores(self, predictions):
        self._predictions = predictions

    def setup_prodict_umap_df(self, df, signatures):
        self._df = df
        self._signatures = signatures

    def setup_immune_status_df(self, df):
        self._df = df

        def classify(x):
            if x >= 2:
                return 2
            elif x >= 1:
                return 1
            else:
                return 0

        sample_order = (
            (self._df.applymap(classify) > 0)
            .sum(axis=1)
            .sort_values(ascending=False)
            .index.to_list()
        )

        sample_order.remove(self._patient)
        self._gene_order = sample_order[:5] + [self._patient] + sample_order[-5:]
        self._df = self._df.loc[self._gene_order]

    def setup_swarm_df(self, df, subcohort_ids):
        self._df = df.melt(
            id_vars="Gene names", var_name="Sample names", value_name="Expression"
        )

        self._df["Is subcohort"] = self._df["Sample names"].isin(subcohort_ids)
        self._df["Is highlighted"] = self._df["Sample names"].eq(self._patient)
        gene_order = (
            self._df[self._df["Is highlighted"]]
            .sort_values("Expression", ascending=False)["Gene names"]
            .tolist()
        )
        self._gene_order = gene_order
        self._subcohort_ids = subcohort_ids

    def generate_swarm_plot(
        self,
        xlabel,
        ylabel,
        title="",
        figsize=(10, 4),
        y_thresh_main=2,
        y_thresh_sec=1.5,
        y_break_at=None,
        ymin=None,
        ymax=None,
        y_outlier_above=None,
    ):
        should_break_axis = (
            y_break_at is not None and (self._df["Expression"] >= y_break_at).sum() > 0
        )
        bottom_plot_idx = 1 if should_break_axis else 0
        nrows = 2 if should_break_axis else 1
        height_ratios = [1, 9] if should_break_axis else None

        self._df["Plot expression"] = self._df["Expression"].apply(
            lambda x: y_outlier_above if y_outlier_above and x >= y_outlier_above else x
        )

        highlight_genes = (
            self._df[self._df["Is highlighted"]]
            .groupby("Gene names")["Expression"]
            .max()
            .gt(y_thresh_main)
        )

        fig, ax = plt.subplots(
            nrows=nrows,
            ncols=1,
            figsize=figsize,
            height_ratios=height_ratios,
            sharex=True,
        )
        fig.subplots_adjust(hspace=0.01)
        ax = np.atleast_1d(ax)

        for x in ax:
            sns.stripplot(
                data=self._df[~self._df["Is subcohort"]],
                x="Gene names",
                y="Plot expression",
                order=self._gene_order,
                color="lightgrey",
                alpha=0.5,
                jitter=True,
                size=3,
                ax=x,
            )

            sns.stripplot(
                data=self._df[self._df["Is subcohort"]],
                x="Gene names",
                y="Plot expression",
                order=self._gene_order,
                color="dodgerblue",
                alpha=0.5,
                jitter=True,
                size=3,
                ax=x,
            )

            sns.stripplot(
                data=self._df[self._df["Is highlighted"]],
                x="Gene names",
                y="Plot expression",
                order=self._gene_order,
                color="red",
                jitter=True,
                size=5,
                ax=x,
            )

            x.set_xlabel(None)
            x.set_ylabel(None)
            x.tick_params(axis="x", which="both", length=0)
            x.tick_params(axis="y", which="both", length=0)

        ax[bottom_plot_idx].axhline(
            y=y_thresh_main, linestyle="--", color="red", zorder=10
        )
        ax[bottom_plot_idx].axhline(
            y=y_thresh_sec, linestyle="--", color="black", alpha=0.3
        )

        ax[bottom_plot_idx].set_xticks(ax[bottom_plot_idx].get_xticks())
        ax[bottom_plot_idx].set_xticklabels(
            ax[bottom_plot_idx].get_xticklabels(),
            rotation=60,
            ha="right",
            rotation_mode="anchor",
        )
        if y_outlier_above:
            yticks = np.arange(
                ymin or ax[bottom_plot_idx].get_yticks()[0], y_outlier_above + 0.5, 0.5
            )
            ax[bottom_plot_idx].set_yticks(yticks)
            ylabels = ax[bottom_plot_idx].get_yticklabels()
            ylabels[-1] = f"≥ {y_outlier_above}"
            ax[bottom_plot_idx].set_yticklabels(ylabels)

            data_to_annot = self._df[
                self._df["Is highlighted"]
                & (self._df["Plot expression"] == y_outlier_above)
            ]
            for _, data in data_to_annot.iterrows():
                ax[bottom_plot_idx].annotate(
                    f'{data["Expression"]:.2f}',
                    (data["Gene names"], y_outlier_above),
                    xytext=(0, 5),
                    textcoords="offset points",
                    fontsize=10,
                    color="red",
                )

        for tick in ax[bottom_plot_idx].get_xticklabels():
            gene = tick.get_text()
            if highlight_genes.get(gene, False):
                tick.set_color("red")

        if should_break_axis:
            max_val = self._df["Expression"].max()
            ax[0].spines.bottom.set_visible(False)
            ax[1].spines.top.set_visible(False)
            ax[0].xaxis.tick_top()
            ax[0].tick_params(labeltop=False)
            ax[1].xaxis.tick_bottom()
            ax[1].set_ylim(bottom=ymin)
            ax[1].set_ylim(top=y_break_at - 0.7)
            ax[0].set_ylim([max_val - 0.3, max_val + 0.3])

            d = 0.5
            kwargs = dict(
                marker=[(-1, -d), (1, d)],
                markersize=12,
                linestyle="none",
                color="k",
                mec="k",
                mew=1,
                clip_on=False,
            )
            ax[0].plot([0, 1], [0, 0], transform=ax[0].transAxes, **kwargs)
            ax[1].plot([0, 1], [1, 1], transform=ax[1].transAxes, **kwargs)
        else:
            ax[0].set_ylim(bottom=ymin)
            ax[0].set_ylim(top=ymax)

        fig.supxlabel(xlabel)
        fig.supylabel(ylabel)
        fig.suptitle(title)
        fig.tight_layout()

        self._fig = fig

    def generate_immune_status_heatmap(self, title):
        cmap = ListedColormap(["aliceblue", "orange", "red"])
        norm = BoundaryNorm([-10, 1.5, 2, 10], cmap.N)
        fig, ax = plt.subplots(figsize=(12, 3))

        sns.heatmap(
            self._df.fillna(0),
            annot=False,
            fmt="",
            cmap=cmap,
            cbar=None,
            linewidths=0.5,
            linecolor="white",
            norm=norm,
            ax=ax,
        )

        mid = len(self._gene_order) // 2
        ax.set_yticks([mid + 0.5])
        ax.set_yticklabels([self._gene_order[mid]])
        ax.set_title(title)

        for label in ax.get_xticklabels():
            label.set_rotation(60)
            label.set_ha("right")
            label.set_rotation_mode("anchor")

        ax.xaxis.label.set_visible(False)
        ax.yaxis.label.set_visible(False)

        fig.tight_layout()
        self._fig = fig

    def generate_umap(
        self,
        title: str,
        n_neighbors: int = 10,
        min_dist: float = 0.1,
        random_state: int = 93,
    ):
        """Generate UMAP visualization with color coding based on signatures and sample"""
        # Get signature values to filter by
        if self._background_cohort not in self._signatures.keys():
            signature_values = [
                item for sublist in self._signatures.values() for item in sublist
            ]
        else:
            signature_values = self._signatures[self._background_cohort]

        # Filter signature specific proteins
        available = self._df.columns.intersection(signature_values)
        X = self._df[available].values
        missing = set(signature_values) - set(self._df.columns)
        if missing:
            print("Missing proteins in dataset, signatures are not complete:", missing)

        # Generate UMAP embedding
        reducer = UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=random_state,
        )
        embedding = reducer.fit_transform(X)

        # Create color array
        colors = []
        for idx in self._df.index:
            if idx == self._patient:
                colors.append("#FF0000")
            elif self._df.loc[idx, "code_oncotree"] == self._background_cohort:
                colors.append("#0468BF")
            else:
                colors.append("silver")

        # Create visualization
        fig, ax = plt.subplots(figsize=(6, 6))

        # Plot points in order
        for color_code, label in [
            ("silver", "Other"),
            ("#0468BF", f"{self._background_cohort}"),
            ("#FF0000", self._patient),
        ]:
            mask = np.array(colors) == color_code
            if np.any(mask):
                ax.scatter(
                    embedding[mask, 0],
                    embedding[mask, 1],
                    c=color_code,
                    label=label,
                    alpha=0.7 if color_code != "#FF0000" else 1.0,
                    s=(
                        60
                        if color_code == "#FF0000"
                        else (75 if color_code == "#0468BF" else 50)
                    ),
                    edgecolors="black" if color_code == "#FF0000" else "white",
                    linewidths=1 if color_code == "#FF0000" else 0.5,
                    zorder=(
                        1
                        if color_code == "silver"
                        else (2 if color_code == "#0468BF" else 3)
                    ),
                )

        ax.set_xlabel("UMAP 1")
        ax.set_ylabel("UMAP 2")
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.legend(loc="best", framealpha=0.9)
        fig.tight_layout()
        self._fig = fig

    def generate_prodict_lollipop(self, title: str):
        """Lollipopo graph to visualize the probabilities of
        each classifier applied to a sample"""
        row = pd.Series(self._predictions).sort_index(ascending=False)

        rename_map = {
            "PLEMESO_PEMESO": "P(L)EMESO",
            "BA_ANGS": "(B)ANGS",
            "LMS_ULMS": "(U)LMS",
            "MEL_UM": "(U)MEL",
        }
        row.index = row.index.to_series().replace(rename_map)

        fig, ax = plt.subplots(figsize=(5, 6))
        ax.hlines(y=row.index, xmin=0, xmax=row.values, color="lightgrey", lw=2)

        # Plot each dot with conditional color
        for feature, value in row.items():
            color = "red" if value > 0.9 else "dodgerblue" if value > 0.5 else "silver"
            ax.plot(value, feature, "o", color=color, markersize=8)

            if value > 0.1:
                ax.text(
                    value + 0.03,
                    feature,
                    f"{value:.2f}",
                    va="center",
                    ha="left",
                    fontsize=9,
                )

        # Add threshold lines
        ax.axvline(x=0.5, color="grey", lw=1, linestyle="--")
        ax.axvline(x=0.9, color="black", lw=1, linestyle="--")

        # Labels
        ax.set_xlabel("Probability")
        ax.set_xticks([0.0, 0.5, 0.9, 1.0])
        ax.set_title(title, fontsize=10, fontweight="bold")

        # Remove frame box (keep only x & y axes)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        # Layout and export as SVG
        fig.tight_layout()
        self._fig = fig

    def output_format(self, id, format, save_cache=True):
        buf = BytesIO()
        self._fig.savefig(buf, format=format, bbox_inches="tight")
        buf.seek(0)
        data = buf.getvalue()
        if save_cache:
            cache.set(id, data, timeout=86400)

        return data

    def close_fig(self):
        plt.close(self._fig)


def preprocess_background_cohort(background_cohort=""):
    return (
        ""
        if background_cohort.strip().lower() in {"", "default", "auto", "none", "null"}
        else background_cohort
    )


def get_background_cohort(
    metadata_df, background_cohort, patient, background_cohort_column="code_oncotree"
):
    metadata_oncotree = metadata_df.get(background_cohort_column)
    preprocessed_background_cohort = preprocess_background_cohort(background_cohort)
    if (
        not preprocessed_background_cohort
        and metadata_oncotree is not None
        and patient in metadata_oncotree.index
    ):
        signature_key = metadata_oncotree.loc[patient]
    else:
        signature_key = preprocessed_background_cohort

    return signature_key


def get_background_cohort_indices(
    metadata_df, column, sample_name, background_cohort=None
):
    if column not in metadata_df.columns:
        return []

    if background_cohort:
        return metadata_df[metadata_df[column] == background_cohort].index.to_list()

    if not sample_name:
        return []

    sample_rows = metadata_df.loc[sample_name]
    if sample_rows.empty:
        return []

    target_class = sample_rows[column]
    return metadata_df[metadata_df[column] == target_class].index.to_list()


# PRODICT


# Load necessary files - Classification models and Tumor Type Signatues
def load_signatures_from_folder(folder_path):
    folder = Path(folder_path)
    signatures_dict = {}

    for file in folder.glob("*.txt"):
        key = file.stem
        with open(file, "r") as f:
            lines = [line.strip() for line in f if line.strip() != ""]
        signatures_dict[key] = lines

    return signatures_dict


def load_sklearn_models(folder_path):
    """Loads pickelized sklearn classification models from folder"""
    models = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".pkl"):
            file_path = os.path.join(folder_path, filename)
            model_name = filename.replace("_log_reg_ridge_model.pkl", "")
            try:
                model = joblib.load(file_path)
                models[model_name] = model
            except Exception as e:
                print(f"{filename} not loaded: {e}")
    return models


def impute_normal_down_shift_distribution(
    unimputed_dataframe: pd.DataFrame,
    column_wise: bool = True,
    width: float = 0.3,
    downshift: float = 1.8,
    seed: int = 2,
) -> pd.DataFrame:
    """
    Performs imputation across a matrix columnswise
    """

    unimputed_df = unimputed_dataframe.copy()
    unimputed_df.replace({pd.NA: np.nan}, inplace=True)
    unimputed_matrix = unimputed_df.to_numpy()
    columns_names = unimputed_df.columns
    rownames = unimputed_df.index

    unimputed_matrix[~np.isfinite(unimputed_matrix)] = np.nan
    main_mean = np.nanmean(unimputed_matrix)
    main_std = np.nanstd(unimputed_matrix)
    np.random.seed(seed=seed)

    def impute_normal_per_vector(temp: np.ndarray, width=width, downshift=downshift):
        """Performs imputation for a single vector"""
        if column_wise:
            temp_sd = np.nanstd(temp)
            temp_mean = np.nanmean(temp)
        else:
            temp_sd = main_std
            temp_mean = main_mean

        shrinked_sd = width * temp_sd
        downshifted_mean = temp_mean - (downshift * temp_sd)
        n_missing = np.count_nonzero(np.isnan(temp))

        if n_missing > 0:
            temp[np.isnan(temp)] = np.random.normal(
                loc=downshifted_mean, scale=shrinked_sd, size=n_missing
            )

        return temp

    final_matrix = np.apply_along_axis(impute_normal_per_vector, 0, unimputed_matrix)
    final_df = pd.DataFrame(final_matrix)
    final_df.index = rownames
    final_df.columns = columns_names

    return final_df


@cache.cached(timeout=300, key_prefix="imputed_cohort_")
def get_imputed_df(cohort_index: int):
    """Collescts intensity dataframe and impute it to further process"""

    fp = cohorts_db.get_protein_abundance_df(
        cohort_index, intensity_unit=IntensityUnit.INTENSITY
    )

    data_initial = fp.T
    imputed_data = impute_normal_down_shift_distribution(
        data_initial, column_wise=True, width=0.3, downshift=1.8, seed=2
    )
    data_clean = imputed_data.dropna(axis=1, how="all")
    return data_clean


# Prediction function


def probabilities_calculator(models: dict, input_data: pd.DataFrame) -> dict:
    """
    Calculates the probability of a sample for every classifier avaialeble
    models: dict of classifier models
    input_data: dict with protein:value pairs (one sample)
    """
    input_df = input_data.copy()  # Convert single sample to DataFrame
    predictions = {}

    for tumor_entity, model in models.items():
        missing_proteins = []

        # Ensure all required proteins exist
        for feature in models[tumor_entity].feature_names_in_:
            if feature not in input_df.columns:
                input_df[feature] = 0
                missing_proteins.append(feature)

        print(f"{len(missing_proteins)} proteins added for {tumor_entity}")

        # Predict probability of class 1
        pred_prob = model.predict_proba(
            input_df[models[tumor_entity].feature_names_in_]
        )[:, 1]
        predictions[tumor_entity] = float(pred_prob)

    return predictions


def can_be_int(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False
