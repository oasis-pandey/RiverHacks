import os


def quiet_third_party_logs():
    # Silence gRPC + absl noise (Gemini libs)
    os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
    os.environ.setdefault("GLOG_minloglevel", "2")
    os.environ.setdefault("ABSL_LOGGING_MIN_LOG_LEVEL", "2")
