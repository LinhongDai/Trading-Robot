import numpy as np
import pandas as pd 

from typing import Any
from typing import List
from typing import Dict
from typing import Union
from typing import Optional
from typing import Tuple

from pyrobot.stock_frame import StockFrame

class Indicators():
    
    def __init__(self, price_data_frame: StockFrame) -> None:

        self._stock_frame: StockFrame = price_data_frame
        self._price_groups = self._stock_frame.symbol_groups 
        self._current_indicators = {}
        self._indicator_signals = {}
        self._frame = self._stock_frame.frame
    
    def set_indicator_signals(self, indicator: str, buy: float, sell: float, condition_buy: Any, condition_sell: Any) -> None:
        """
        Sets buy and sell signals for a given indicator

        Args:
            indicator: Name of the indicator.
            buy: Threshold for buy signal.
            sell: Threshold for sell signal.
            condition_buy: Condition for triggering buy signal.
            condition_sell: Condition for triggering sell signal.

        """
        # If there is no signal
        if indicator not in self._indicator_signals:
            self._indicator_signals[indicator] = {}

        # Modify the signal
        self._indicator_signals[indicator]['buy'] = buy
        self._indicator_signals[indicator]['sell'] = sell
        self._indicator_signals[indicator]['buy_operator'] = condition_buy
        self._indicator_signals[indicator]['sell_operator'] = condition_sell

    def get_indicator_signals(self, indicator: Optional[str]) -> Dict:
        """
        Retrieves signals for a specific indicator or all indicators

        Args:
            indicator (Optional[str]): Name of the indicator (optional)

        Returns:
            Dict:  dictionary of signals
        """
        if indicator and indicator in self._indicator_signals:
            return self._indicator_signals[indicator]
        else:
            return self._indicator_signals
        
    @property
    def price_data_frame(self) -> pd.DataFrame:
        """_summary_

        Returns:
            pd.DataFrame: _description_
        """
        return self._frame
    
    @price_data_frame.setter
    def price_data_frame(self, price_data_frame: pd.DataFrame) -> None:
        """_summary_

        Args:
            price_data_frame (pd.DataFrame): _description_
        """
        self._frame = price_data_frame

    def change_in_price(self) -> pd.DataFrame:
        """
        culates the change in price and adds it as a new column to the DataFrame.
        Stores the arguments and function reference in self._current_indicators

        Returns:
            pd.DataFrame: _description_
        """
        locals_data = locals()
        del locals_data['self']

        column_name = 'change_in_price'
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.change_in_price

        self._frame[column_name] = self._price_groups['close'].transform(
            lambda x: x.diff()
        )

    def rsi(self, period: int, method: str = 'wilders') -> pd.DataFrame:
        """_summary_

        Args:
            period (int): _description_
            method (str, optional): _description_. Defaults to 'wilders'.

        Returns:
            pd.DataFrame: _description_
        """
        locals_data = locals()
        del locals_data['self']

        column_name = 'rsi'
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.rsi

        if 'change_in_price' not in self._frame.columns:
            self.change_in_price()

        # Define the up days
            self._frame['up_day'] = self._price_groups['change_in_price'].transform(
                lambda x : np.where(x >=0, x, 0)
            )
        # Define the down days
            self._frame['down_day'] = self._price_groups['change_in_price'].transform(
                lambda x : np.where(x < 0, x.abs(), 0)
            )

            self._frame['ewma_up'] = self._price_groups['up_day'].transform(
                lambda x : x.ewm(span=period).mean()
            )

            relative_strength = self._frame['ewma_up'] / self._frame['ewma_down']

            relative_strength_index = 100 - (100.0 / (1.0 + relative_strength))

            # Add the RSI indicator to the data frame
            self._frame['rsi'] = np.where(relative_strength_index == 0, 100, 100.0 - (100.0 / (1.0 + relative_strength)))

            # clean up  before sendig back
            self._frame.drop(
                labels=['ewma_up', 'ewma_down', 'down_day', 'up_day', 'change_in_price'],
                axis=1,
                inplace=True
            )

            return self._frame
        
    def sma(self, period: int) -> pd.DataFrame:
        """_summary_

        Args:
            period (int): _description_

        Returns:
            pd.DataFrame: _description_
        """
        locals_data = locals()
        del locals_data['self']

        column_name = 'sma'
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.sma

        # Add the SMA
        self._frame[column_name] = self._price_groups['close'].transform(
            lambda x: x.rolling(window=period).mean()
        )

        return self._frame
    
    def ema(self, period: int, alpha: float = 0.0, column_name = 'ema') -> pd.DataFrame:
        """Calculates the Exponential Moving Average (EMA).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating the EMA.

        alpha {float} -- The alpha weight used in the calculation. (default: {0.0})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the EMA indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.ema(period=50, alpha=1/50)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.ema

        # Add the EMA
        self._frame[column_name] = self._price_groups['close'].transform(
            lambda x: x.ewm(span=period).mean()
        )

        return self._frame
    
    def refresh(self):
        """
        ensures that all the technical indicators stored in 
        self._current_indicators are recalculated using the latest price data.
        """
        # First update the groups
        self._price_groups = self._stock_frame.symbol_groups

        # Loop through all the stored indicators
        for indicator in self._current_indicators:

            indicator_arguments = self._current_indicators[indicator]['args']
            indicator_function = self._current_indicators[indicator]['func']

            # update the columns
            indicator_function(**indicator_arguments)

    def check_signals(self) -> Union[pd.DataFrame, None]:
        """_summary_

        Returns:
            Union[pd.DataFrame, None]: _description_
        """
        signals_df = self._stock_frame._check_signals(indicators=self._indicator_signals)

        return signals_df