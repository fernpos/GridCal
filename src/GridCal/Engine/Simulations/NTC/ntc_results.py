import numpy as np
import pandas as pd

from GridCal.Engine.Simulations.result_types import ResultTypes
from GridCal.Engine.Simulations.results_table import ResultsTable
from GridCal.Engine.Simulations.results_template import ResultsTemplate

from GridCal.Engine.Devices.enumerations import TransformerControlType, HvdcControlType


def add_exchange_sensibilities(y, columns, alpha, mc_idx=None, alpha_n1=None):
    """
    :param y: report data matrix
    :param columns: report column names
    :param mc_idx: Idx tuple (monitor, contingency) for contingency flows
    :return: Extended y, columns with required data
    """

    if y.shape[0] == 0:
        # empty data, return
        return y, columns


    if mc_idx:
        # unzip monitor and contingency lists
        m, c = list(map(list, zip(*np.array(mc_idx))))

    else:
        m = np.arange(len(alpha))

    y_ = np.array([
        alpha[m],  # Alpha: sensibility to exchange power
    ], dtype=object).T

    y = np.concatenate([y, y_], axis=1)

    columns.extend([
        'Alpha',
    ])

    if alpha_n1 is not None:
        # Worst alpha for monitorized branch
        # idx_c = np.argmax(np.abs(alpha_n1), axis=1)
        # alpha_c = np.take_along_axis(alpha_n1, np.expand_dims(idx_c, axis=1), axis=1)[m]

        # Alpha for contingency branch
        # alpna_c = np.array([alpha_n1[m, c]]).T

        # y_ = np.array([
        #     # alpha_n1[m, c],  # Alpha: sensibility to exchange power in contingency situation
        #     alpna_max[m, :],  # Worst alpha for monitorized branch
        # ], dtype=object).T

        alpha_c = alpha_n1[m]
        y = np.concatenate([y, alpha_c], axis=1)

        columns.extend([
            # 'Alpha n-1',
            '|Worst alpha n-1| ',
        ])

    return y, columns


def add_maczt(y, columns, trm, ttc):
    """
    Add MACZT data (margin available for cross-zonal trade)
    :param y: report data matrix
    :param columns: report column names
    :param ttc: Total transfer capacity
    :param trm: Transmission reliability margin
    :return: Extended y, columns with required data
    """

    if y.shape[0] == 0:
        # empty data, return
        return y, columns

    alpha_col = list(map(lambda c: c.lower(), columns)).index('alpha')
    rate_col = list(map(lambda c: c.lower(), columns)).index('rate')

    trm = np.ones(y.shape[0]) * trm
    ttc = np.ones(y.shape[0]) * np.floor(ttc)
    ntc = ttc - trm

    maczt = ntc * [np.abs(y[:, alpha_col]) / y[:, rate_col]]

    y = np.concatenate([y, maczt.T], axis=1)

    columns.extend([
        'MACZT',
    ])

    return y, columns


def add_min_ntc(y, columns, ntc_load_rule):
    """
    Add minimun ntc to be considered as critial element
    :param y: report data matrix
    :param columns: report column names
    :param ntc_load_rule: percentage of rate reserved to exchange purposes
    :return: Extended y, columns with required data
    """

    if y.shape[0] == 0:
        # empty data, return
        return y, columns

    alpha_col = list(map(lambda c: c.lower(), columns)).index('alpha')
    rate_col = list(map(lambda c: c.lower(), columns)).index('rate')

    # avoid numerical zero
    alpha = y[:, alpha_col]
    alpha[alpha == 0] = 1e-20

    min_ntc = np.array([y[:, rate_col] / np.abs(alpha) * ntc_load_rule])

    y = np.concatenate([y, min_ntc.T], axis=1)

    columns.extend([
        'NTC min'
    ])

    return y, columns


def add_ntc_data(y, columns, ttc, trm):
    """
    Add ntc info data into y, columns from report
    :param y: report data matrix
    :param columns: report column names
    :param ttc: Total transfer capacity
    :param trm: Transmission reliability margin
    :return: Extended y, columns with required data
    """

    if y.shape[0] == 0:
        # empty data, return
        return y, columns

    trm = np.ones(y.shape[0]) * trm
    ttc = np.ones(y.shape[0]) * np.floor(ttc)
    ntc = ttc - trm

    y_ = np.array([trm, ttc, ntc]).T
    y = np.concatenate([y, y_], axis=1)

    columns.extend([
        'TRM',
        'TTC',
        'NTC',
    ])

    return y, columns

class OptimalNetTransferCapacityResults(ResultsTemplate):
    """
    OPF results.
    Arguments:
        **Sbus**: bus power injections
        **voltage**: bus voltages
        **load_shedding**: load shedding values
        **Sf**: branch power values
        **overloads**: branch overloading values
        **loading**: branch loading values
        **losses**: branch losses
        **converged**: converged?
    """

    def __init__(self,
                 bus_names,
                 branch_names,
                 load_names,
                 generator_names,
                 battery_names,
                 hvdc_names,
                 trm,
                 ntc_load_rule,
                 branch_control_modes,
                 hvdc_control_modes,
                 Sbus=None,
                 voltage=None,
                 battery_power=None,
                 controlled_generation_power=None,
                 Sf=None,
                 loading=None,
                 losses=None,
                 solved=None,
                 bus_types=None,
                 hvdc_flow=None,
                 hvdc_loading=None,
                 hvdc_angle_slack=None,
                 phase_shift=None,
                 generation_delta=None,
                 inter_area_branches=None,
                 inter_area_hvdc=None,
                 alpha=None,
                 alpha_n1=None,
                 rates=None,
                 contingency_branch_flows_list=None,
                 contingency_branch_indices_list=None,
                 contingency_generation_flows_list=None,
                 contingency_generation_indices_list=None,
                 contingency_hvdc_flows_list=None,
                 contingency_hvdc_indices_list=None,
                 contingency_rates=None,
                 branch_ntc_load_rule=None,
                 area_from_bus_idx=None,
                 area_to_bus_idx=None,
                 contingency_branch_alpha_list=None,
                 contingency_generation_alpha_list=None,
                 contingency_hvdc_alpha_list=None,
                 structural_ntc=None,
                 sbase=None,
                 monitor=None,
                 monitor_loading=None,
                 monitor_by_sensitivity=None,
                 monitor_by_unrealistic_ntc=None,
                 monitor_by_zero_exchange=None,
                 loading_threshold=0.0,
                 reversed_sort_loading=True,
                 ):

        ResultsTemplate.__init__(
            self,
            name='OPF',
            available_results={
                ResultTypes.FlowReports: [
                    ResultTypes.ContingencyFlowsReport,
                    ResultTypes.ContingencyFlowsBranchReport,
                    ResultTypes.ContingencyFlowsGenerationReport,
                    ResultTypes.ContingencyFlowsHvdcReport,
                ],
                ResultTypes.BusResults: [
                    ResultTypes.BusVoltageModule,
                    ResultTypes.BusVoltageAngle,
                ],
                ResultTypes.BranchResults: [
                    ResultTypes.BranchPower,
                    ResultTypes.BranchLoading,
                    ResultTypes.BranchTapAngle,
                    ResultTypes.BranchMonitoring
                ],
                ResultTypes.HvdcResults: [
                    ResultTypes.HvdcPowerFrom,
                ],
                ResultTypes.DispatchResults: [
                    ResultTypes.BatteryPower,
                    ResultTypes.GeneratorPower,
                    ResultTypes.GenerationDelta,
                ],
                ResultTypes.AreaResults: [
                    ResultTypes.AvailableTransferCapacityAlpha,
                    ResultTypes.AvailableTransferCapacityAlphaN1,
                    ResultTypes.InterAreaExchange,
                ]
            },
            data_variables=[
                'bus_names',
                'branch_names',
                'load_names',
                'generator_names',
                'battery_names',
                'Sbus',
                'voltage',
                'Sf',
                'bus_types',
                'overloads',
                'loading',
                'battery_power',
                'generator_power',
                'converged'
            ]
        )

        self.bus_names = bus_names
        self.branch_names = branch_names
        self.load_names = load_names
        self.generator_names = generator_names
        self.battery_names = battery_names
        self.hvdc_names = hvdc_names

        self.trm = trm
        self.ntc_load_rule = ntc_load_rule

        self.hvdc_control_modes = hvdc_control_modes
        self.branch_control_modes = branch_control_modes

        self.inter_area_branches = inter_area_branches or list()
        self.inter_area_hvdc = inter_area_hvdc or list()

        self.area_from_bus_idx = area_from_bus_idx
        self.area_to_bus_idx = area_to_bus_idx

        self.generation_delta = generation_delta

        self.Sbus = Sbus

        self.voltage = voltage

        self.Sf = Sf

        self.hvdc_Pf = hvdc_flow
        self.hvdc_loading = hvdc_loading
        self.hvdc_angle_slack = hvdc_angle_slack

        self.phase_shift = phase_shift

        self.bus_types = bus_types

        self.loading = loading

        self.losses = losses

        self.battery_power = battery_power

        self.generator_power = controlled_generation_power

        self.solved = solved

        self.alpha = alpha
        self.alpha_n1 = alpha_n1

        self.monitor = monitor
        self.monitor_loading = monitor_loading
        self.monitor_by_sensitivity = monitor_by_sensitivity
        self.monitor_by_unrealistic_ntc = monitor_by_unrealistic_ntc
        self.monitor_by_zero_exchange = monitor_by_zero_exchange

        self.contingency_branch_flows_list = contingency_branch_flows_list
        self.contingency_branch_indices_list = contingency_branch_indices_list  # [(t, m, c), ...]
        self.contingency_branch_alpha_list = contingency_branch_alpha_list

        self.contingency_generation_flows_list = contingency_generation_flows_list
        self.contingency_generation_indices_list = contingency_generation_indices_list  # [(t, m, c), ...]
        self.contingency_generation_alpha_list = contingency_generation_alpha_list

        self.contingency_hvdc_flows_list = contingency_hvdc_flows_list
        self.contingency_hvdc_indices_list = contingency_hvdc_indices_list  # [(t, m, c), ...]
        self.contingency_hvdc_alpha_list = contingency_hvdc_alpha_list

        self.rates = rates
        self.contingency_rates = contingency_rates

        self.branch_ntc_load_rule = branch_ntc_load_rule

        self.structural_ntc = structural_ntc

        self.sbase = sbase

        self.plot_bars_limit = 100

        self.loading_threshold = loading_threshold
        self.reversed_sort_loading = reversed_sort_loading

        self.reports = dict()

    def apply_new_rates(self, nc: "SnapshotData"):
        rates = nc.Rates
        self.loading = self.Sf / (rates + 1e-9)

    def initialize(self, n, m):
        """
        Initialize the arrays
        @param n: number of buses
        @param m: number of branches
        @return:
        """
        self.Sbus = np.zeros(n, dtype=complex)

        self.voltage = np.zeros(n, dtype=complex)

        self.Sf = np.zeros(m, dtype=complex)

        self.loading = np.zeros(m, dtype=complex)

        self.losses = np.zeros(m, dtype=complex)

        self.converged = list()

        self.plot_bars_limit = 100

    def get_exchange_power(self):
        y = list()

        for (k, sign) in self.inter_area_branches:
            y.append([self.Sf[k] * sign])

        for (k, sign) in self.inter_area_hvdc:
            y.append([self.hvdc_Pf[k] * sign])

        return np.array(y).sum()

    def create_contingency_report(self, loading_threshold=0.98, reverse=True):

        title = f'{ResultTypes.ContingencyFlowsReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        # Gel all contingency reports. All they are returned as tuples (y, columns, labels)
        b = self.get_contingency_branch_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        g = self.get_contingency_generation_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        h = self.get_contingency_hvdc_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )

        # Group all, but only if they are not empty
        labels, y_list = list(), list()
        for i, mdl in enumerate([b, g, h]):
            if mdl.get_data()[2].shape[0] != 0:
                labels.extend(mdl.get_data()[0])
                y_list.extend(mdl.get_data()[2])

        columns = mdl.get_data()[1]
        y = np.array(y_list)
        labels = np.array(labels)

        c_name = [c for c in columns if 'contingency' in c.lower() and '%' in c.lower()][0]

        # sort if necessary
        y, labels = apply_sort(
            y=y,
            labels=labels,
            col=columns.index(c_name),
            reverse=reverse,
        )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='',
            xlabel='',
            units='',
        )

    def create_monitoring_logic_report(self):
        """
        Get flow report
        """

        title = ResultTypes.BranchMonitoring.value[0]

        y = np.array([
            self.monitor,  # Monitor result
            self.monitor_loading,  # Monitor loading by user
            self.monitor_by_sensitivity,  # Monitor by sensibility
            self.monitor_by_unrealistic_ntc,  # Monitor by unrealistic ntc
            self.monitor_by_zero_exchange,  # Monitor by zero exchange load
            self.rates,  # Rates
            self.contingency_rates,  # Contingency rates
        ], dtype=object).T

        labels = self.branch_names
        columns = [
            'Monitor',
            'By model',
            'By exchange sensibility',
            'By unrealistic NTC',
            'By zero exchange',
            'Rate',
            'Contingency rate',
        ]

        # Add exchange sensibilities
        y, columns = add_exchange_sensibilities(
            y=y,
            columns=columns,
            alpha=self.alpha,
        )

        # Add MACZT (margin available for cross-zonal trade) data
        y, columns = add_maczt(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add min ntc to be considered as critical element
        y, columns = add_min_ntc(
            y=y,
            columns=columns,
            ntc_load_rule=self.ntc_load_rule,
        )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='(p.u.)',
            xlabel='',
            units='',
        )

    def create_base_report(self, loading_threshold, reverse):
        """
        Get base report
        :param loading_threshold: threshold to filter results,
        :param reverse: Boolean to get ordered results. None to keep original .
        """

        title = f'{ResultTypes.BaseFlowReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        labels, columns, y = get_flow_table(
            m=np.arange(len(self.branch_names)),
            flow=self.Sf,
            rates=self.rates,
            monitor_names=self.branch_names,
            contingency_names=self.branch_names,
        )

        # Add exchange sensibilities
        y, columns = add_exchange_sensibilities(
            y=y,
            columns=columns,
            alpha=self.alpha,
        )

        # Add TTC, TRM and NTC
        y, columns = add_ntc_data(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add interarea branches data
        y, columns = add_inter_area_branches_data(
            y=y,
            columns=columns,
            inter_area_branches=self.inter_area_branches,
            Sf=self.Sf,
            names=self.branch_names,
        )

        # Add hvdc branches data
        y, columns = add_hvdc_data(
            y=y,
            columns=columns,
            hvdc_Pf=self.hvdc_Pf,
            hvdc_names=self.hvdc_names,
        )

        # Add controlled shifter data
        y, columns = self.add_shifter_data(
            y=y,
            columns=columns,
            controlled_shifters=self.get_controlled_shifters_as_pt(),
            phase_shift=self.phase_shift,
        )

        # filter results if required
        if loading_threshold != 0.0:
            y, labels = apply_filter(
                y=y,
                labels=labels,
                col=columns.index('Load %'),
                threshold=loading_threshold,
            )

        # sort by column value
        if reverse is not None:
            y, labels = apply_sort(
                y=y,
                labels=labels,
                col=columns.index('Load %'),
                reverse=reverse,
            )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='',
            xlabel='',
            units='',
        )

    def create_contingency_branch_report(self, loading_threshold, reverse):
        """
        Get branch contingency report
        :param loading_threshold: threshold to filter results,
        :param reverse: Boolean to get ordered results. None to keep original .
        """

        title = f'{ResultTypes.ContingencyFlowsBranchReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        labels, columns, y = get_contingency_flow_table(
            mc_idx=self.contingency_branch_indices_list,
            flow=self.Sf,
            contingency_flow=self.contingency_branch_flows_list,
            monitor_names=self.branch_names,
            contingency_names=self.branch_names,
            rates=self.rates,
            contingency_rates=self.contingency_rates
        )

        # Add exchange sensibilities
        y, columns = add_exchange_sensibilities(
            y=y,
            columns=columns,
            mc_idx=self.contingency_branch_indices_list,
            alpha=self.alpha,
            alpha_n1=self.alpha_n1,
        )

        # Add TTC, TRM and NTC
        y, columns = add_ntc_data(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add MACZT (margin available for cross-zonal trade) data
        y, columns = add_maczt(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add min ntc to be considered as critical element
        y, columns = add_min_ntc(
            y=y,
            columns=columns,
            ntc_load_rule=self.ntc_load_rule,
        )

        # Add interarea branches data
        y, columns = add_inter_area_branches_data(
            y=y,
            columns=columns,
            inter_area_branches=self.inter_area_branches,
            Sf=self.Sf,
            names=self.branch_names,
        )

        # Add hvdc branches data
        y, columns = add_hvdc_data(
            y=y,
            columns=columns,
            hvdc_Pf=self.hvdc_Pf,
            hvdc_names=self.hvdc_names,
        )

        # Add controlled shifter data
        y, columns = self.add_shifter_data(
            y=y,
            columns=columns,
            controlled_shifters=self.get_controlled_shifters_as_pt(),
            phase_shift=self.phase_shift,
        )

        c_name = [c for c in columns if 'contingency' in c.lower() and '%' in c.lower()][0]

        # filter results if required
        if loading_threshold != 0.0:

            y, labels = apply_filter(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                threshold=loading_threshold,
            )

        # sort by column value
        if reverse is not None:
            y, labels = apply_sort(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                reverse=reverse,
            )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='',
            xlabel='',
            units='',
        )

    def create_contingency_generation_report(self, loading_threshold, reverse):
        """
        Get generation contingency report
        :param loading_threshold: threshold to filter results,
        :param reverse: Boolean to get ordered results. None to keep original .
        """
        title = f'{ResultTypes.ContingencyFlowsGenerationReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'


        labels, columns, y = get_contingency_flow_table(
            mc_idx=self.contingency_generation_indices_list,
            flow=self.Sf,
            contingency_flow=self.contingency_generation_flows_list,
            monitor_names=self.branch_names,
            contingency_names=self.generator_names,
            rates=self.rates,
            contingency_rates=self.contingency_rates
        )

        # Add exchange sensibilities
        y, columns = add_exchange_sensibilities(
            y=y,
            columns=columns,
            mc_idx=self.contingency_generation_indices_list,
            alpha=self.alpha,
            alpha_n1=self.alpha_n1,  #todo: check how to do it
        )

        # Add TTC, TRM and NTC
        y, columns = add_ntc_data(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add MACZT (margin available for cross-zonal trade) data
        y, columns = add_maczt(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add min ntc to be considered as critical element
        y, columns = add_min_ntc(
            y=y,
            columns=columns,
            ntc_load_rule=self.ntc_load_rule,
        )

        # Add interarea branches data
        y, columns = add_inter_area_branches_data(
            y=y,
            columns=columns,
            inter_area_branches=self.inter_area_branches,
            Sf=self.Sf,
            names=self.branch_names,
        )

        # Add hvdc branches data
        y, columns = add_hvdc_data(
            y=y,
            columns=columns,
            hvdc_Pf=self.hvdc_Pf,
            hvdc_names=self.hvdc_names,
        )

        # Add controlled shifter data
        y, columns = self.add_shifter_data(
            y=y,
            columns=columns,
            controlled_shifters=self.get_controlled_shifters_as_pt(),
            phase_shift=self.phase_shift,
        )

        c_name = [c for c in columns if 'contingency' in c.lower() and '%' in c.lower()][0]

        # filter results if required
        if loading_threshold != 0.0:
            y, labels = apply_filter(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                threshold=loading_threshold,
            )

        # sort by column value
        if reverse is not None:
            y, labels = apply_sort(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                reverse=reverse,
            )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='',
            xlabel='',
            units='',
        )

    def create_contingency_hvdc_report(self, loading_threshold, reverse):
        """
        Get hvdc contingency report
        :param loading_threshold: threshold to filter results,
        :param reverse: Boolean to get ordered results. None to keep original .
        """

        title = f'{ResultTypes.ContingencyFlowsHvdcReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        labels, columns, y = get_contingency_flow_table(
            mc_idx=self.contingency_hvdc_indices_list,
            flow=self.Sf,
            contingency_flow=self.contingency_hvdc_flows_list,
            monitor_names=self.branch_names,
            contingency_names=self.hvdc_names,
            rates=self.rates,
            contingency_rates=self.contingency_rates
        )

        # Add exchange sensibilities
        y, columns = add_exchange_sensibilities(
            y=y,
            columns=columns,
            mc_idx=self.contingency_hvdc_indices_list,
            alpha=self.alpha,
            alpha_n1=self.alpha_n1, #todo: check how to do it
        )

        # Add TTC, TRM and NTC
        y, columns = add_ntc_data(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add MACZT (margin available for cross-zonal trade) data
        y, columns = add_maczt(
            y=y,
            columns=columns,
            ttc=self.get_exchange_power(),
            trm=self.trm,
        )

        # Add min ntc to be considered as critical element
        y, columns = add_min_ntc(
            y=y,
            columns=columns,
            ntc_load_rule=self.ntc_load_rule,
        )

        # Add interarea branches data
        y, columns = add_inter_area_branches_data(
            y=y,
            columns=columns,
            inter_area_branches=self.inter_area_branches,
            Sf=self.Sf,
            names=self.branch_names,
        )

        # Add hvdc branches data
        y, columns = add_hvdc_data(
            y=y,
            columns=columns,
            hvdc_Pf=self.hvdc_Pf,
            hvdc_names=self.hvdc_names,
        )

        # Add controlled shifter data
        y, columns = self.add_shifter_data(
            y=y,
            columns=columns,
            controlled_shifters=self.get_controlled_shifters_as_pt(),
            phase_shift=self.phase_shift,
        )

        c_name = [c for c in columns if 'contingency' in c.lower() and '%' in c.lower()][0]

        # Apply filters
        if loading_threshold != 0.0:
            y, labels = apply_filter(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                threshold=loading_threshold,
            )

        # Apply sort
        if reverse is not None:
            y, labels = apply_sort(
                y=y,
                labels=labels,
                col=columns.index(c_name),
                reverse=reverse,
            )

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=columns,
            title=title,
            ylabel='(p.u.)',
            xlabel='',
            units='',
        )

    def create_interarea_exchange_report(self):

        title = ResultTypes.InterAreaExchange.value[0]

        labels = list()
        y = list()

        for (k, sign) in self.inter_area_branches:
            labels.append(self.branch_names[k])
            y.append([self.Sf[k] * sign])

        for (k, sign) in self.inter_area_hvdc:
            labels.append(self.hvdc_names[k])
            y.append([self.hvdc_Pf[k] * sign])

        y.append([np.array(y).sum()])
        y = np.array(y)
        labels = np.array(labels + ['Total'])

        self.reports[title] = ResultsTable(
            data=y,
            index=labels,
            columns=['Exchange'],
            title=title,
            ylabel='(MW)',
            xlabel='',
            units='',
        )

    def create_all_reports(self, loading_threshold, reverse):
        self.create_contingency_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        self.create_contingency_branch_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        self.create_contingency_generation_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        self.create_contingency_hvdc_report(
            loading_threshold=loading_threshold,
            reverse=reverse,
        )
        self.create_monitoring_logic_report()
        self.create_interarea_exchange_report()

    def get_controlled_shifters_as_pt(self):
        shifter_idx = np.where(self.branch_control_modes == TransformerControlType.Pt)
        shifter_names = self.branch_names[shifter_idx]

        return shifter_idx, shifter_names

    def add_shifter_data(self, y, columns, controlled_shifters, phase_shift):
        """
        Add shifter data into y, columns from report
        :param y: report data matrix
        :param columns: report column names
        :param controlled_shifters: Tuple (idx, name) for each controlled shifter
        :param phase_shift: branches phase shift
        :return:
        """
        if y.shape[0] == 0:
            # empty data, return
            return y, columns

        idx, names = controlled_shifters
        y_ = np.array([phase_shift[idx]] * y.shape[0])
        y = np.concatenate([y, y_], axis=1)
        columns.extend(names)
        return y, columns

    def make_report(self, path_out=None):
        """

         :param path_out:
         :return:
         """

        print('NTC is', self.get_exchange_power(), 'MW')

        mdl = self.get_contingency_full_report(
            loading_threshold=0.98,
            reverse=True,
        )

        # Save file
        if path_out:
            mdl.to_df().to_csv(
                path_or_buf=path_out,
                index=False
            )

    def mdl(self, result_type) -> "ResultsTable":
        """
        Plot the results
        :param result_type: type of results (string)
        :return: DataFrame of the results (or None if the result was not understood)
        """

        if result_type == ResultTypes.BusVoltageModule:
            return ResultsTable(
                data=np.abs(self.voltage),
                index=self.bus_names,
                columns=['V (p.u.)'],
                title=result_type.value[0],
                ylabel='(p.u.)',
            )

        elif result_type == ResultTypes.BusVoltageAngle:
            return ResultsTable(
                data=np.angle(self.voltage),
                index=self.bus_names,
                columns=['V (radians)'],
                title=result_type.value[0],
                ylabel='(radians)',
            )

        elif result_type == ResultTypes.BranchPower:
            return ResultsTable(
                data=self.Sf.real,
                columns=['Sf'],
                index=self.branch_names,
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.BusPower:
            return ResultsTable(
                data=self.loading * 100.0,
                index=self.Sbus.real,
                columns=['Sb'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.BranchLoading:
            return ResultsTable(
                data=self.loading * 100.0,
                index=self.branch_names,
                columns=['Loading'],
                title=result_type.value[0],
                ylabel='(%)',
            )

        elif result_type == ResultTypes.BranchOverloads:
            return ResultsTable(
                data=np.abs(self.overloads),
                index=self.branch_names,
                columns=['Loading'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.BranchLosses:
            return ResultsTable(
                data=self.losses.real,
                index=self.branch_names,
                columns=['PLosses'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.BranchTapAngle:
            return ResultsTable(
                data=np.rad2deg(self.phase_shift),
                index=self.branch_names,
                columns=['V (deg)'],
                title=result_type.value[0],
                ylabel='(deg)',
            )

        elif result_type == ResultTypes.GeneratorPower:
            return ResultsTable(
                data=self.generator_power,
                index=self.generator_names,
                columns=['P'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.BatteryPower:
            return ResultsTable(
                data=self.battery_power,
                index=self.battery_names,
                columns=['P'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        elif result_type == ResultTypes.HvdcPowerFrom:
            return ResultsTable(
                data=self.hvdc_Pf,
                index=self.hvdc_names,
                columns=['Pf'],
                title=result_type.value[0],
                ylabel='(MW)',
            )

        # elif result_type == ResultTypes.HvdcPmode3Slack:
        #    labels = self.hvdc_names
        #    y = self.hvdc_angle_slack
        #    y_label = '(rad)'
        #    title = result_type.value[0]

        elif result_type == ResultTypes.AvailableTransferCapacityAlpha:
            return ResultsTable(
                data=self.alpha,
                index=self.branch_names,
                title=result_type.value[0],
                columns=['Sensitivity'],
                ylabel='(p.u.)',
                xlabel='',
                units='',
            )

        elif result_type == ResultTypes.AvailableTransferCapacityAlphaN1:
            return ResultsTable(
                data=self.alpha_n1,
                index=self.branch_names,
                columns=self.branch_names,
                title=result_type.value[0],
                ylabel='(p.u.)',
                xlabel='',
                units='',
            )

        elif result_type == ResultTypes.GenerationDelta:
            return ResultsTable(
                data=self.generation_delta,
                index=self.generator_names,
                columns=['P'],
                title=result_type.value[0],
                ylabel='(MW)',
                xlabel='',
                units='',
            )

        elif result_type == ResultTypes.BranchMonitoring:
            return self.get_monitoring_logic_report()

        elif result_type == ResultTypes.InterAreaExchange:
            return self.get_interarea_exchange_report()

        elif result_type == ResultTypes.ContingencyFlowsReport:
            return self.get_contingency_full_report(
                loading_threshold=self.loading_threshold,
                reverse=self.reversed_sort_loading,
            )

        elif result_type == ResultTypes.ContingencyFlowsBranchReport:
            return self.get_contingency_hvdc_report(
                loading_threshold=self.loading_threshold,
                reverse=self.reversed_sort_loading,
            )

        elif result_type == ResultTypes.ContingencyFlowsGenerationReport:
            return self.get_contingency_generation_report(
                loading_threshold=self.loading_threshold,
                reverse=self.reversed_sort_loading,
            )

        elif result_type == ResultTypes.ContingencyFlowsHvdcReport:
            return self.get_contingency_hvdc_report(
                loading_threshold=self.loading_threshold,
                reverse=self.reversed_sort_loading,
            )

        else:
            return ResultsTable(
                data=np.zeros(0),
                index=np.zeros(0).shape[0] * [''],
                columns=np.zeros(0).shape[0] * [''],
            )


    def get_monitoring_logic_report(self):
        title = ResultTypes.BranchMonitoring.value[0]

        if title not in self.reports.keys():
            self.create_monitoring_logic_report()

        return self.reports[title]

    def get_base_report(self, loading_threshold=0.0, reverse=True):

        title = f'{ResultTypes.BaseFlowReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        if title not in self.reports.keys():
            self.create_base_report(
                loading_threshold=loading_threshold,
                reverse=reverse,
            )
        return self.reports[title]

    def get_contingency_full_report(self, loading_threshold=0.0, reverse=True):

        title = f'{ResultTypes.ContingencyFlowsReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        if title not in self.reports.keys():
            self.create_contingency_report(
                loading_threshold=loading_threshold,
                reverse=reverse,
            )
        return self.reports[title]

    def get_contingency_branch_report(self, loading_threshold=0.0, reverse=True):

        title = f'{ResultTypes.ContingencyFlowsBranchReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        if title not in self.reports.keys():
            self.create_contingency_branch_report(
                loading_threshold=loading_threshold,
                reverse=reverse,
            )
        return self.reports[title]
    def get_contingency_generation_report(self, loading_threshold=0.0, reverse=True):

        title = f'{ResultTypes.ContingencyFlowsBranchReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        if title not in self.reports.keys():
            self.create_contingency_generation_report(
                loading_threshold=loading_threshold,
                reverse=reverse,
            )

        return self.reports[title]

    def get_contingency_hvdc_report(self, loading_threshold=0.0, reverse=True):

        title = f'{ResultTypes.ContingencyFlowsHvdcReport.value[0]}. ' \
                f'Loading threshold: {str(loading_threshold)}. ' \
                f'Reverse: {str(reverse)}'

        if title not in self.reports.keys():
            self.create_contingency_hvdc_report(
                loading_threshold=loading_threshold,
                reverse=reverse,
            )

        return self.reports[title]

    def get_interarea_exchange_report(self):
        title = ResultTypes.InterAreaExchange.value[0]

        if title not in self.reports.keys():
            self.create_interarea_exchange_report()

        return self.reports[title]

def add_hvdc_data(y, columns, hvdc_Pf, hvdc_names):
    """
    Add hvdc data into y, columns from report
    :param y: report data matrix
    :param columns: report column names
    :param hvdc_Pf: HVDC Powers from
    :param hvdc_names: HVDC names
    :return:
    """
    if y.shape[0] == 0:
        # empty data, return
        return y, columns

    # add hvdc power
    y_ = np.array([hvdc_Pf] * y.shape[0])
    y = np.concatenate((y, y_), axis=1)
    columns.extend(hvdc_names)
    return y, columns


def add_inter_area_branches_data(y, columns, inter_area_branches, names, Sf):
    """
    Add inter area branches data into y, columns from report
    :param y: report data matrix
    :param columns: report column names
    :param inter_area_branches: inter area branches
    :param Sf: Branch powers from
    :param names: branch names
    :return:
    """
    if y.shape[0] == 0:
        # empty data, return
        return y, columns

    idx, senses = list(map(list, zip(*inter_area_branches)))

    y_ = np.array([Sf[idx]] * y.shape[0])
    y = np.concatenate([y, y_], axis=1)
    columns.extend(names[idx])
    return y, columns


def apply_sort(y, labels, col, reverse=False):
    """
    Sort by column
    """
    # sort by column value
    if y.shape[0] > 0:
        idx = np.argsort(np.abs(y[:, col].astype(float)))

        if reverse:
            idx = np.flip(idx)
            y = y[idx]
            labels = labels[idx]

    return y, labels


def get_contingency_flow_table(
        mc_idx, flow, contingency_flow, monitor_names, contingency_names,
        rates, contingency_rates
):
    """
    Get flow report
    :param mc_idx: Idx tuple (monitor, contingency) for contingency flows
    :param flow: Array with flows
    :param contingency_flow: Array with contingency flows
    :param monitor_names: Array with full list of monitor element names
    :param contingency_names: Array with full list of contingency element names
    :param rates: Rates array
    :param contingency_rates: Contingency rates array

    """

    columns = [
        'Monitored',
        'Contingency',
        'Flow',
        'Load %',
        'Rate',
        'Contingency flow',
        'Contingency flow %',
        'Contingency rate',
    ]

    if len(mc_idx) == 0:
        labels = []
        y = np.array([])
        return labels, columns, y

    # unzip monitor and contingency lists
    m, c = list(map(list, zip(*np.array(mc_idx))))

    y = np.array([
        monitor_names[m],
        contingency_names[c],  # Contingency name
        flow[m].real,  # Branch flow
        np.round(flow[m] / rates[m] * 100, 2),  # Branch loading
        rates[m],  # Rates
        contingency_flow.real,  # Contingency flow
        np.round(contingency_flow / contingency_rates[m] * 100, 2),  # Contingency loading
        contingency_rates[m],  # Contingency rates
    ], dtype=object).T

    labels = monitor_names[m]

    return labels, columns, y


def get_flow_table(m, flow, rates, monitor_names, contingency_names):
    """
    Get flow report
    :param m: monitor indices
    :param monitor_names: full monitor element names
    :param contingency_names: full contingency element names
    returns
    """
    y = np.array([
        contingency_names[m],  # Contingency names
        flow[m].real,  # Branch flow
        np.round(flow[m] / rates[m] * 100, 2),  # Branch loading
        rates[m],  # Rates
    ], dtype=object).T

    labels = monitor_names[m]

    columns = [
        'Branch',
        'Flow',
        'Load %',
        'Rate',
    ]

    return labels, columns, y


def apply_filter(y, labels, col, threshold):
    if y.shape[0] == 0:
        return y, labels

    idx = np.where(np.abs(y[:, col]) >= threshold)
    return y[idx], labels[idx]

