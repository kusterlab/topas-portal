from typing import Any, Dict, Optional, Protocol, Type

import numpy as np
import numpy.typing as npt
import pandas as pd
from numba.core.errors import NumbaDeprecationWarning
import warnings

warnings.simplefilter("ignore", category=NumbaDeprecationWarning)

from phate import PHATE
from ppca import PPCA
from sklearn.preprocessing import StandardScaler
from umap import UMAP

from sklearn.decomposition import PCA
from typing import Tuple, List



FloatArray = npt.NDArray[np.float64]


class CohortDimensionalityReduction(Protocol):
    _fit_performed: bool
    _imputed_data: pd.DataFrame
    _dim_object: Any

    def fit(self, x: pd.DataFrame) -> None:
        ...

    def fit_transform(self, x: pd.DataFrame) -> pd.DataFrame:
        ...

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        ...

    def get_explained_variances(self) -> Optional[FloatArray]:
        ...


def impute_missing_values_with_min(
    df: pd.DataFrame, print_warning: bool = True
) -> pd.DataFrame:
    if df.isnull().sum().sum() == 0:
        return df

    if print_warning:
        print(
            "Warning: NaN values detected, imputing with minimum value. "
            "To impute missing values during PCA calculation, use fit_transform instead."
        )
    return df.fillna(df.min().min())



def _impute_and_scale(df: pd.DataFrame) -> pd.DataFrame:
    df = impute_missing_values_with_min(df)
    df = StandardScaler().fit_transform(df)
    return pd.DataFrame(df)


class CohortPCA:
    def __init__(self, n_components: int = 2):
        self._n_components = n_components

        self._dim_object = PCA(n_components=self._n_components)

        self._fit_performed = False
        self._imputed_data = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        df = _impute_and_scale(df)
        self._dim_object.fit(df)
        self._fit_performed = True

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = _impute_and_scale(df)
        self.fit(df)
        self._fit_performed = True
        return self.transform(df)

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        assert self._fit_performed, "Fitting must be done before PCA transform"
        return pd.DataFrame(self._dim_object.transform(x))

    def get_explained_variances(self) -> FloatArray:
        assert self._fit_performed, "Fitting must be done before getting loadings"
        explained_variance: FloatArray = self._dim_object.explained_variance_ratio_
        return explained_variance


class CohortPPCA:
    def __init__(self, n_components: int = 2):
        self._n_components = n_components

        self._dim_object = PPCA()

        self._fit_performed = False
        self._imputed_data = pd.DataFrame()

    def fit(self, df: pd.DataFrame) -> None:
        df = np.array(df)
        self._dim_object.fit(data=df, d=self._n_components, verbose=False)
        self._imputed_data = pd.DataFrame(self._dim_object.data)
        self._fit_performed = True

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.fit(df)
        return pd.DataFrame(self._dim_object.transform())

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        assert self._fit_performed, "Fitting must be done before PCA transform"
        df = impute_missing_values_with_min(df)
        return pd.DataFrame(self._dim_object.transform(df.values))

    def get_explained_variances(self) -> FloatArray:
        assert self._fit_performed, "Fitting must be done before PCA transform"
        explained_variance: FloatArray = self._dim_object.var_exp
        explained_variance[1] = explained_variance[1] - explained_variance[0]
        return explained_variance


class CohortUMAP:
    def __init__(
        self,
        n_components: int = 2,
        n_epochs: int = 1000,
        n_neighbors: int = 10,
        metric: str = "euclidean",
        n_components_ppca: int = 2,
        random_state: int = 42,
    ):
        self._n_components_ppca = n_components_ppca
        self._n_components_umap = n_components
        self._n_epochs = n_epochs
        self._n_neigh = n_neighbors
        self._metric = metric

        self._fit_performed = False
        self._imputed_data = pd.DataFrame()

        np.random.seed(random_state)
        self._ppca = PPCA()
        self._dim_object = UMAP(
            n_components=self._n_components_umap,
            n_epochs=self._n_epochs,
            n_neighbors=self._n_neigh,
            metric=self._metric,
            low_memory=True,
            random_state=random_state,
        )

    def fit(self, df: pd.DataFrame) -> None:
        self._ppca.fit(data=df.values, d=self._n_components_ppca, verbose=False)
        self._imputed_data = pd.DataFrame(self._ppca.data)

        self._dim_object.fit(self._imputed_data)
        self._fit_performed = True

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.fit(df)
        return self.transform(self._imputed_data)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        assert self._fit_performed, "Fitting must be done before UMAP transform"
        df = impute_missing_values_with_min(df)
        return pd.DataFrame(self._dim_object.transform(df))

    def get_explained_variances(self) -> None:
        return None


class CohortPHATE:
    def __init__(self, n_components_ppca: int = 2):
        self._n_components_ppca = n_components_ppca

        self._imputed_data = pd.DataFrame()
        self._fit_performed: bool = False

        self._ppca = PPCA()
        self._dim_object = PHATE()

    def fit(self, df: pd.DataFrame) -> None:
        self._ppca.fit(data=df.values, d=self._n_components_ppca, verbose=False)
        self._imputed_data = pd.DataFrame(self._ppca.data)

        self._dim_object.fit(X=self._imputed_data)
        self._fit_performed = True

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        self.fit(df)
        return self.transform(self._imputed_data)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        assert self._fit_performed, "Fitting must be done before PHATE transform"
        df = impute_missing_values_with_min(df)
        return pd.DataFrame(self._dim_object.transform(df))

    def get_explained_variances(self) -> None:
        return None


def get_dimensionality_reduction_method(
    plot_type: str,
) -> CohortDimensionalityReduction:
    plot_type = plot_type.upper()

    factories: Dict[str, Type[CohortDimensionalityReduction]] = {
        "PCA": CohortPCA,
        "PPCA": CohortPPCA,
        "UMAP": CohortUMAP,
        "PHATE": CohortPHATE,
    }
    if plot_type not in factories.keys():
        raise NotImplementedError

    return (factories[plot_type])()




def get_pca_objects(
    dfs: List[pd.DataFrame], pct_threshold: List[float]
) -> Tuple[List, List]:
    """Wrapper for calling pca calculation function for each df given"""
    pca_objects_list = []
    for df in dfs:
        df = df.transpose()
        pca_object, x = calculate_pcas(df, pct_threshold=pct_threshold)
        pca_objects_list.append(pca_object)
    return pca_objects_list, x



def calculate_pcas(
    df: pd.DataFrame, pct_threshold: List[float] = [0.5]
) -> Tuple[List, List]:
    """
    Calculate PCA or PPCA of given df with given threshold
    Threshold 50 means that to consider the proteins which are in at least 50% of the patients
    """
    all_x, pcas = [], []
    for i, pct in enumerate(pct_threshold):
        # define dataframe with threshold and transform it
        x = df.loc[:, df.count(axis=0) >= df.shape[0] * pct]
        x = StandardScaler().fit_transform(x)
        all_x.append(x)

        ppca = PPCA()
        ppca.fit(data=x, d=2, verbose=False)
        # change cumulated explained variance to just variance per PC
        ppca.var_exp[1] = ppca.var_exp[1] - ppca.var_exp[0]
        pcas.append(ppca)
    if len(pcas) == 1:
        pcas = pcas[0]
    return pcas, ppca.var_exp