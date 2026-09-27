from .engine import ScreenerEngine


class ScreenerPresets(ScreenerEngine):
    """
    Collection of ready-made preset screeners.

    Each preset simply defines custom filter values and
    reuses the generic apply_filters() method from
    ScreenerEngine.
    """

    def quality_compounder(self, df):
        """
        High-quality businesses with good profitability,
        efficient asset utilization, positive cash flow,
        and consistent growth.
        """

        filters = {
            "opm_min": 15,
            "roa_min": 10,
            "asset_turnover_min": 1,
            "fcf_min": 0,
            "revenue_cagr_min": 10,
            "pat_cagr_min": 10
        }

        return self.apply_filters(df, filters)

    # -----------------------------------------------------

    def growth_accelerator(self, df):
        """
        Fast-growing companies.
        """

        filters = {
            "revenue_cagr_min": 15,
            "pat_cagr_min": 15,
            "eps_cagr_min": 15,
            "fcf_min": 0
        }

        return self.apply_filters(df, filters)

    # -----------------------------------------------------

    def cash_generator(self, df):
        """
        Companies generating positive free cash flow.
        """

        filters = {
            "fcf_min": 0,
            "icr_min": 2
        }

        return self.apply_filters(df, filters)

    # -----------------------------------------------------

    def asset_efficient(self, df):
        """
        Companies efficiently utilizing assets.
        """

        filters = {
            "asset_turnover_min": 1,
            "opm_min": 10
        }

        return self.apply_filters(df, filters)

    # -----------------------------------------------------

    def high_quality(self, df):
        """
        High composite quality score companies.
        """

        result = df.copy()

        if "composite_quality_score" not in result.columns:
            return result.reset_index(drop=True)

        result = result[
            result["composite_quality_score"] >= 70
        ]

        result = result.drop_duplicates(
            subset=["company_id"],
            keep="last"
        )

        result = result.sort_values(
            by="composite_quality_score",
            ascending=False
        )

        return result.reset_index(drop=True)

    # -----------------------------------------------------

    def turnaround_watch(self, df):
        """
        Companies showing signs of turnaround.
        """

        filters = {
            "revenue_cagr_min": 5,
            "pat_cagr_min": 5,
            "fcf_min": 0
        }

        return self.apply_filters(df, filters)
    
        # -----------------------------------------------------

    def run_preset(self, preset_name, df):
        """
        Execute the selected preset screener.

        Parameters
        ----------
        preset_name : str
            Name of the preset selected by the user.

        df : pandas.DataFrame
            Financial ratios DataFrame.

        Returns
        -------
        pandas.DataFrame
            Filtered screener results.
        """

        presets = {
            "Quality Compounder": self.quality_compounder,
            "Growth Accelerator": self.growth_accelerator,
            "Cash Generator": self.cash_generator,
            "Asset Efficient": self.asset_efficient,
            "High Quality": self.high_quality,
            "Turnaround Watch": self.turnaround_watch,
        }

        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")

        return presets[preset_name](df)