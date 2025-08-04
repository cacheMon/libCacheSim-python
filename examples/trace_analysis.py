import libcachesim as lcs

# Step 1: Get one trace from S3 bucket
URI = "cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
dl = lcs.DataLoader()
dl.load(URI)

reader = lcs.TraceReader(
    trace=dl.get_cache_path(URI),
    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=False),
)

analysis_option = lcs.AnalysisOption(
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

analysis_param = lcs.AnalysisParam()

analyzer = lcs.TraceAnalyzer(reader, "example_analysis", analysis_option=analysis_option, analysis_param=analysis_param)

analyzer.run()
