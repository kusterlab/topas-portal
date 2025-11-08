import pandas as pd

from topas_portal.utils import (
    merge_by_delimited_field,
)  # replace with your actual module path


def test_merge_by_delimited_field_basic():
    # Input dataframe
    df = pd.DataFrame(
        {"genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"], "other_annot": ["AAA", "BBB"]}
    )

    # Lookup dataframe
    mapping = pd.DataFrame(
        {
            "genes": ["TP53", "BRCA1", "EGFR", "KRAS", "BRAF"],
            "pathway": ["P53", "BRCA", "EGFR", "MAPK", "RAF"],
        }
    )

    # Expected outcome: each gene maps to its pathway, merged back by id
    expected = pd.DataFrame(
        {
            "genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"],
            "pathway": ["P53;BRCA", "EGFR;MAPK;RAF"],
            "other_annot": ["AAA", "BBB"],
        }
    )

    result = merge_by_delimited_field(df, mapping, field_name="genes")

    # Check that results match
    pd.testing.assert_frame_equal(
        result, expected, check_like=True, check_index_type=False
    )


def test_merge_by_delimited_field_index_col():
    # Input dataframe
    df = pd.DataFrame(
        {"genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"], "other_annot": ["AAA", "BBB"]}
    ).set_index("genes")

    # Lookup dataframe
    mapping = pd.DataFrame(
        {
            "genes": ["TP53", "BRCA1", "EGFR", "KRAS", "BRAF"],
            "pathway": ["P53", "BRCA", "EGFR", "MAPK", "RAF"],
        }
    )

    # Expected outcome: each gene maps to its pathway, merged back by id
    expected = pd.DataFrame(
        {
            "genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"],
            "pathway": ["P53;BRCA", "EGFR;MAPK;RAF"],
            "other_annot": ["AAA", "BBB"],
        }
    )

    result = merge_by_delimited_field(df, mapping, field_name="genes")

    # Check that results match
    pd.testing.assert_frame_equal(
        result, expected, check_like=True, check_index_type=False
    )


def test_merge_by_delimited_field_inplace():
    # Input dataframe
    df = pd.DataFrame(
        {"genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"], "other_annot": ["AAA", "BBB"]}
    )

    # Lookup dataframe
    mapping = pd.DataFrame(
        {
            "genes": ["TP53", "BRCA1", "EGFR", "KRAS", "BRAF"],
            "pathway": ["P53", "BRCA", "EGFR", "MAPK", "RAF"],
        }
    )

    # Expected outcome: each gene maps to its pathway, merged back by id
    expected = pd.DataFrame(
        {
            "genes": ["TP53;BRCA1", "EGFR;KRAS;BRAF"],
            "pathway": ["P53;BRCA", "EGFR;MAPK;RAF"],
            "other_annot": ["AAA", "BBB"],
        }
    )

    merge_by_delimited_field(df, mapping, field_name="genes", inplace=True)

    # Check that results match
    pd.testing.assert_frame_equal(df, expected, check_like=True, check_index_type=False)


def test_merge_by_delimited_field_duplicates():
    # Input dataframe
    df = pd.DataFrame(
        {
            "genes": ["TP53;BRCA1", "TP53;BRCA1", "EGFR;KRAS;BRAF"],
            "other_annot": ["AAA", "BBB", "CCC"],
        }
    )

    # Lookup dataframe
    mapping = pd.DataFrame(
        {
            "genes": ["TP53", "BRCA1", "EGFR", "KRAS", "BRAF"],
            "pathway": ["P53", "BRCA", "EGFR", "MAPK", "RAF"],
        }
    )

    # Expected outcome: each gene maps to its pathway, merged back by id
    expected = pd.DataFrame(
        {
            "genes": ["TP53;BRCA1", "TP53;BRCA1", "EGFR;KRAS;BRAF"],
            "pathway": ["P53;BRCA", "P53;BRCA", "EGFR;MAPK;RAF"],
            "other_annot": ["AAA", "BBB", "CCC"],
        }
    )

    result = merge_by_delimited_field(df, mapping, field_name="genes")

    # Check that results match
    pd.testing.assert_frame_equal(
        result, expected, check_like=True, check_index_type=False
    )


def test_merge_by_delimited_field_handles_missing_values():
    df = pd.DataFrame({"genes": ["TP53;UNKNOWN"]})

    mapping = pd.DataFrame({"genes": ["TP53"], "pathway": ["P53"]})

    result = merge_by_delimited_field(df, mapping, field_name="genes")

    # Missing entries should result in NaN in merged columns
    assert "UNKNOWN" in result["genes"].iloc[0]
    assert result["pathway"].iloc[0] == "P53"


def test_merge_by_delimited_field_empty_df():
    df = pd.DataFrame(columns=["id", "genes"]).set_index("id")
    mapping = pd.DataFrame(columns=["genes", "pathway"])

    result = merge_by_delimited_field(df, mapping, "genes")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
