"""
Stock and activity of the vehicle fleet of Andorra, from the Excel register of ITV.

    python main.py --settings settings_2026                  # calculation and charts
    python main.py --settings settings_2026 --stage calculate
    python main.py --settings settings_2026 --stage charts   # charts from the aggregated tables already calculated
    python main.py --settings settings_2026 --stage export   # files for LEAP (needs the results of COPERT)
    python main.py --settings settings_2026 --stage upload   # Google Cloud Storage and BigQuery

Stages: calculate -> charts -> export -> upload (all = calculate + charts)
"""
import argparse
import logging

from Logger import setup_logger
from pipeline import load_settings, OutputPaths

STAGES = ['all', 'calculate', 'charts', 'export', 'upload']


def parse_arguments(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--settings', default='settings_2026',
                        help='name of the python module with the settings of the study (default: settings_2026)')
    parser.add_argument('--stage', default='all', choices=STAGES, help='stage to run (default: all)')
    parser.add_argument('--show', action='store_true', help='open the charts in the browser')
    parser.add_argument('--copert-results', default=None,
                        help='csv file with the electricity demand calculated by COPERT (stage export)')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_arguments(argv)
    settings = load_settings(args.settings)
    paths = OutputPaths(settings)
    paths.create_folders()

    # Create and initialize loggers (the output folder must exist)
    setup_logger('logger', paths.debug_log)
    setup_logger('info_logger', paths.info_log, stream=False)
    logger = logging.getLogger('logger')
    logger.info(f'Started. Settings: {args.settings}, stage: {args.stage}')

    if args.stage in ('all', 'calculate'):
        from pipeline.calculation import run_calculation
        run_calculation(settings, paths)
    if args.stage in ('all', 'charts'):
        from pipeline.charts_stage import run_charts
        run_charts(settings, paths, show=args.show)
    if args.stage == 'export':
        from exports.leap import run_leap_export
        run_leap_export(settings, paths, args.copert_results)
    if args.stage == 'upload':
        from cloud.upload import run_upload
        run_upload(settings, paths)
    logger.info('end')


if __name__ == '__main__':
    main()
