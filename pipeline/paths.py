from pathlib import Path


class OutputPaths:
    """
    Output folders and file names of a study. Convention: lowercase, ASCII, no spaces,
    <content>_<study year>_<AAAAMMDD of the extraction of the register>.<extension>, inside
    output/<AAAAMMDD>/{curated, aggregated, qa, charts, exports}
    """

    def __init__(self, settings):
        self.snapshot = settings.SNAPSHOT_DATE.strftime('%Y%m%d')
        self.study_year = settings.STUDY_YEAR
        self.tag = f'{self.study_year}_{self.snapshot}'
        self.root = Path(settings.BASE_FOLDER) / settings.OUTPUT_FOLDER / self.snapshot
        self.curated = self.root / 'curated'
        self.aggregated = self.root / 'aggregated'
        self.qa = self.root / 'qa'
        self.charts = self.root / 'charts'
        self.exports_copert = self.root / 'exports' / 'copert'
        self.exports_leap = self.root / 'exports' / 'leap'

    def create_folders(self):
        for folder in (self.curated, self.aggregated, self.qa, self.charts, self.exports_copert, self.exports_leap):
            folder.mkdir(parents=True, exist_ok=True)

    # Logs
    @property
    def debug_log(self) -> Path:
        return self.root / f'debug_{self.study_year}.log'

    @property
    def info_log(self) -> Path:
        return self.root / f'info_{self.study_year}.log'

    # Curated: one row per vehicle
    @property
    def fleet_vehicles_csv(self) -> Path:
        return self.curated / f'fleet_vehicles_{self.tag}.csv'

    @property
    def fleet_vehicles_parquet(self) -> Path:
        return self.curated / f'fleet_vehicles_{self.tag}.parquet'

    # Aggregated tables
    @property
    def stock_activity(self) -> Path:
        return self.aggregated / f'fleet_stock_activity_{self.tag}.csv'

    @property
    def stock_by_manufacturing_year(self) -> Path:
        return self.aggregated / f'fleet_stock_by_manufacturing_year_{self.tag}.csv'

    @property
    def stock_by_registration_year(self) -> Path:
        return self.aggregated / f'fleet_stock_by_registration_year_{self.tag}.csv'

    # Quality assurance
    @property
    def qa_passenger_cars_cc_out_of_range(self) -> Path:
        return self.qa / f'qa_passenger_cars_cc_out_of_range_{self.tag}.csv'

    @property
    def qa_l_category_cc_out_of_range(self) -> Path:
        return self.qa / f'qa_l_category_cc_out_of_range_{self.tag}.csv'

    @property
    def qa_activity_outliers(self) -> Path:
        return self.qa / f'qa_activity_outliers_{self.tag}.csv'

    @property
    def qa_km_decreasing_between_itv(self) -> Path:
        return self.qa / f'qa_km_decreasing_between_itv_{self.tag}.csv'

    # Charts
    def chart(self, name: str) -> Path:
        return self.charts / f'chart_{name}_{self.tag}.html'

    @property
    def charts_index(self) -> Path:
        return self.charts / 'index.html'

    # Exports
    @property
    def copert_stock_activity(self) -> Path:
        return self.exports_copert / f'copert_stock_activity_{self.tag}.csv'

    @property
    def leap_electricity_demand(self) -> Path:
        return self.exports_leap / f'leap_electricity_demand_{self.tag}.xlsx'
