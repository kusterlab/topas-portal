import pytest
import pandas as pd
import topas_portal.correlations_preprocess as cp


def test_get_correlations(correlation_dfs):
    # the correaltion of a single vector with all vectors of a matrix
    # at least 8 points must exist for comparison
    res = cp.get_correlations(
        correlation_dfs["marix_df"], correlation_dfs["single_vector_df"]
    )

    res = res.set_index("index")
    # protein A with B
    assert res.loc["proteinB", "correlation"] == 1  # correlation of the proteiB
    assert res.loc["proteinB", "num_patients"] == 8  #
    assert res.loc["proteinB", "p-value"] == 0  #
    assert res.loc["proteinB", "abs_correlation"] == 1  #
    assert res.loc["proteinB", "rank"] == 1  #
    assert res.loc["proteinB", "FDR"] == 0  #
    # protein A with C
    assert (
        res.loc["proteinC", "correlation"] == 0.3860004834656276
    )  # correlation of the proteiB
    assert res.loc["proteinC", "num_patients"] == 8  #
    assert res.loc["proteinC", "p-value"] == 0.34492649129700514  #
    assert res.loc["proteinC", "abs_correlation"] == 0.3860004834656276  #
    assert res.loc["proteinC", "rank"] == 2  #
    assert res.loc["proteinC", "FDR"] == 0.34492649129700514  #
    assert len(res.index) == 2
    # checking for the error D


@pytest.fixture
def correlation_dfs():
    """
    Returns a dictionary with
    :matrixdf :a matrix of 3 proteins(B,C,D) over 9 patients as a pandas data frame
    :single_vector_df: a vector of proteinA over 9 proteins as a pandas data frame
    """
    df1 = pd.DataFrame(
        {"ProteinA": [1.1, 2.2, None, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9]}
    ).transpose()
    df1.columns = [f"patient{i}" for i in range(len(df1.columns))]

    df2 = pd.DataFrame(
        {  # Proteins  B    C   D
            "patient0": [1.1, 4.2, 3.4],
            "patient1": [2.2, 11.1, 1.4],
            "patient2": [3.3, None, 1.9],
            "patient3": [4.4, 19.1, 6.4],
            "patient4": [5.5, 13.7, None],
            "patient5": [6.6, 18.8, 7.4],
            "patient6": [7.7, 10.4, 2.4],
            "patient7": [8.8, 14.3, None],
            "patient8": [9.9, 12.3, 1.4],
        }
    )
    df2.index = ["proteinB", "proteinC", "proteinD"]

    print(df2)
    return {"single_vector_df": df1, "marix_df": df2}
