from abc import ABC, abstractmethod


class ExchangeRateProvider(ABC):

    @abstractmethod
    def usd_to_cop(self) -> float:
        pass
