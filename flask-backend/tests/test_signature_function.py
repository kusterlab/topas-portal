import pytest
import pandas as pd
from topas_portal.signature_function import one_vs_all_t_test


# Sample input data for testing
@pytest.fixture
def input_df():
    data = {
        "Patient_ID": [1, 2, 3, 4, 5],
        "Protein_A": [1.2, 2.3, 3.4, 4.5, 5.6],
        "Protein_B": [0.5, 1.5, 2.5, 3.5, 4.5],
        "Meta_Column": ["A", "B", "A", "C", "B"],
    }
    return pd.DataFrame(data)


# Test cases
def test_one_vs_all_t_test(input_df):
    # Test case 1: Ensure correct computation and output format
    protein_peptide = ["Protein_A", "Protein_B"]
    favorite_entity = "A"
    meta_data_column = "Meta_Column"

    result_df = one_vs_all_t_test(
        input_df, protein_peptide, favorite_entity, meta_data_column
    )

    expected_df = pd.DataFrame(
        {
            "t_statistics": {0: -1.224744871391589, 1: -1.2247448713915892},
            "p_values": {0: 0.308068009250357, 1: 0.308068009250357},
            "means_group1": {0: 2.3, 1: 1.5},
            "means_group2": {0: 4.133333333333333, 1: 3.1666666666666665},
            "num_samples_groups_interest": {0: 2, 1: 2},
            "num_sample_other_groups": {0: 3, 1: 3},
            "Gene Names": {0: "Protein_A", 1: "Protein_B"},
            "fdr": {0: 0.308068009250357, 1: 0.308068009250357},
            "up_down": {0: "down", 1: "down"},
        }
    )

    pd.testing.assert_frame_equal(expected_df, result_df)

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.shape[0] == len(protein_peptide)
    assert all(
        col in result_df.columns
        for col in [
            "t_statistics",
            "p_values",
            "means_group1",
            "means_group2",
            "num_samples_groups_interest",
            "num_sample_other_groups",
            "Gene Names",
            "fdr",
            "up_down",
        ]
    )


def test_one_vs_all_t_test_missing_values(input_df):
    # Test case 2: Ensure correct handling of missing values
    protein_peptide = ["Protein_A", "Protein_B"]
    favorite_entity = "A"
    meta_data_column = "Meta_Column"

    input_df.loc[2, "Protein_A"] = None  # introduce missing value
    result_df = one_vs_all_t_test(
        input_df, protein_peptide, favorite_entity, meta_data_column
    )

    expected_df = pd.DataFrame(
        {
            "t_statistics": {0: -1.5118578920369086, 1: -1.2247448713915892},
            "p_values": {0: 0.26970325665977846, 1: 0.308068009250357},
            "means_group1": {0: 1.2, 1: 1.5},
            "means_group2": {0: 4.133333333333333, 1: 3.1666666666666665},
            "num_samples_groups_interest": {0: 1, 1: 2},
            "num_sample_other_groups": {0: 3, 1: 3},
            "Gene Names": {0: "Protein_A", 1: "Protein_B"},
            "fdr": {0: 0.308068009250357, 1: 0.308068009250357},
            "up_down": {0: "down", 1: "down"},
        }
    )

    pd.testing.assert_frame_equal(expected_df, result_df)

    assert (
        result_df.isnull().values.any() == False
    )  # Ensure there are no NaN values in the result

    # Add more test cases as needed
