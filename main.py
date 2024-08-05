from __future__ import annotations

import logging
import json
import warnings
from datetime import datetime
from pathlib import Path

import argparse
# `json_fix` should not be removed it enables the __json__ to be the handler for json.dump & json.dumps
import json_fix

from experiments.batch_experiment import BatchExperiment
from experiments.experiment import Experiment
from experiments.loggers.logger import ConsoleHandler, CsvFileHandler, OurLogger


def __init_logging_system(
        log_path: str,
        json_df_path: str,
        json_df_save: bool = False,
        console_show=True,
        level=logging.INFO

):
    logging.setLoggerClass(OurLogger)
    logger = logging.getLogger()
    logger.setLevel(level)
    console = ConsoleHandler()
    console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    console.setLevel(level)
    logger.setLevel(level)
    if json_df_save and json_df_path:
        log_csv_path = json_df_path
        df_handler = CsvFileHandler(f'{log_csv_path}')
        df_handler.setLevel(logging.DEBUG)
        logger.addHandler(df_handler)
    if console_show:
        logger.addHandler(console)
    if log_path:
        _log_path = Path(log_path)
        if _log_path.is_dir():
            _log_path.mkdir(exist_ok=True, parents=True)
            _log_path = _log_path / f'{datetime.now().strftime("%Y%m%d%H%M%S")}.log'
        else:
            _log_path.parent.mkdir(exist_ok=True, parents=True)
            _log_path.touch(exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
    if level == logging.DEBUG:
        warnings.filterwarnings("default")

    return logger


def _arguments_parsing():
    parser = argparse.ArgumentParser(
        prog="SAUCE",
        description="Synchronous and Asynchronous User-Customizable Environment for Multi-Agent LLM Interaction",
    )
    parser.add_argument(
        "config",
        type=argparse.FileType(),
        help="what config to run"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType(mode="w"),
        default=str(Path("./output_files/out.json")),
        help="Where to save the experiment output"
    )
    parser.add_argument(
        "--json",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="boolean field indicting rather saved or not to save a json version of the logs"
    )
    parser.add_argument(
        "--output-json",
        dest="out_json",
        type=str,
        required=False,
        default=str(Path(".") / "output_files" / f"output.json"),
        help="File where to save the json form of the raw logs",
    )
    parser.add_argument(
        "-c",
        "--console",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable output to std output"
    )
    parser.add_argument(
        "--output-log",
        dest="out_log",
        type=str,
        required=False,
        default=str(Path(".") / "logs" / f"output.log"),
        help="Where to save the created log"
    )

    parser.add_argument(
        "--batch-mode",
        "-bm",
        dest="batch_mode",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Change the running exp to use Batch mode person"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action=argparse.BooleanOptionalAction,
    )

    return parser.parse_args()


if __name__ == '__main__':
    arguments = _arguments_parsing()
    logger = __init_logging_system(
        log_path=arguments.out_log,
        json_df_save=arguments.json,
        json_df_path=arguments.out_json,
        level=logging.DEBUG if arguments.verbose else logging.INFO
    )
    # conf_path = "./test/test_config.json"
    logger.info(f"open config from {arguments.config.name}")
    # with open(conf_path, 'r') as file:
    conf_json = json.load(arguments.config)
    logger.debug(f"Loaded {conf_json}")
    logger.info("Creating experiment object")
    experiment_cls = Experiment if not arguments.batch_mode else BatchExperiment
    exp: Experiment | None = None
    try:
        exp = experiment_cls.load_from_string(json.dumps(conf_json))
    except Exception:
        logger.exception("Unable to load experiment")
    logger.info("running experiment")
    experiment_output = None
    try:
        experiment_output = exp.run()
    except Exception:
        logger.exception("Unhandled exception while running experiment")
    if experiment_output:
        json.dump(experiment_output, arguments.output, indent=4)
