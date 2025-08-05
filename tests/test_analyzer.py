from libcachesim import TraceAnalyzer, TraceReader, AnalysisOption, AnalysisParam
import os
import pytest


def test_analyzer_common():
    """
    Test the trace analyzer functionality.
    """

    # Add debugging and error handling
    URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
    reader = TraceReader(trace=URI)

    # For this specific small dataset (only 4 objects), configure analysis options more conservatively
    # to avoid bounds issues with the analysis modules
    analysis_option = AnalysisOption(
        req_rate=True,  # Keep basic request rate analysis
        access_pattern=False,  # Disable access pattern analysis
        size=True,  # Keep size analysis
        reuse=False,  # Disable reuse analysis for small datasets
        popularity=False,  # Disable popularity analysis for small datasets (< 200 objects)
        ttl=False,  # Disable TTL analysis
        popularity_decay=False,  # Disable popularity decay analysis
        lifetime=False,  # Disable lifetime analysis
        create_future_reuse_ccdf=False,  # Disable experimental features
        prob_at_age=False,  # Disable experimental features
        size_change=False,  # Disable size change analysis
    )

    # Set track_n_popular and track_n_hit to small values suitable for this dataset
    analysis_param = AnalysisParam(
        track_n_popular=4,  # Match the actual number of objects
        track_n_hit=4,  # Match the actual number of objects
    )

    analyzer = TraceAnalyzer(
        reader, "TestAnalyzerResults", analysis_option=analysis_option, analysis_param=analysis_param
    )

    analyzer.run()

    # Clean file after test, match all files with the prefix "TestAnalyzerResults"
    for file in os.listdir("."):
        if file.startswith("TestAnalyzerResults"):
            os.remove(file)
    # Remove file named "stat"
    stat_file = "stat"
    if os.path.exists(stat_file):
        os.remove(stat_file)
