from typing import Callable, Optional

from app.domain.model.hardware_benchmark import HardwareBenchmark
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)
from app.domain.ports.hardware_benchmark_repository import (
    HardwareBenchmarkRepository,
)
from app.domain.services.cpu_classifier import classify_cpu, cpu_level_from_score
from app.domain.services.gpu_classifier import classify_gpu, level_from_score

# Nivel de cada componente frente a los requisitos.
INSUFFICIENT = "insufficient"
MINIMUM = "minimum"
RECOMMENDED = "recommended"
UNKNOWN = "unknown"


def _level(yours, minimum, recommended) -> str:
    if yours is None or minimum is None:
        return UNKNOWN

    if yours < minimum:
        return INSUFFICIENT

    # Si la fuente no publica un recomendado válido, basta con el mínimo.
    if recommended is None or recommended < minimum:
        recommended = minimum

    return RECOMMENDED if yours >= recommended else MINIMUM


def _required_reference(
    benchmarks: Optional[HardwareBenchmarkRepository],
    text: Optional[str],
) -> Optional[HardwareBenchmark]:
    """
    Puntaje de referencia de un requisito.

    Cuando el requisito enumera varios modelos ("GTX 1060 o RX 580"), se usa
    el promedio de sus puntajes: tomar el más débil vuelve el requisito
    demasiado permisivo si el benchmark castiga a uno de ellos.
    """

    if not benchmarks:
        return None

    mentioned = benchmarks.find_in_text(text)

    if not mentioned:
        return None

    if len(mentioned) == 1:
        return mentioned[0]

    names = sorted(item.name for item in mentioned)

    return HardwareBenchmark(
        name="promedio de " + ", ".join(names[:-1]) + " y " + names[-1],
        score=round(sum(item.score for item in mentioned) / len(mentioned)),
        laptop=all(item.laptop for item in mentioned),
    )


class _Component:
    """Lo que hace falta para comparar una gráfica o un procesador."""

    def __init__(
        self,
        name: str,
        benchmarks: Optional[HardwareBenchmarkRepository],
        classify: Callable[[Optional[str]], Optional[int]],
        level_from_benchmark: Callable[[int], int],
    ):
        self.name = name
        self.benchmarks = benchmarks
        self.classify = classify
        self.level_from_benchmark = level_from_benchmark

    def user_benchmark(self, model: Optional[str]) -> Optional[HardwareBenchmark]:
        if not self.benchmarks or not model:
            return None

        return self.benchmarks.get_by_name(model)

    def recognized_level(self, model: Optional[str]) -> Optional[int]:
        """Nivel por familia de modelo o, si es un modelo nuevo, por su puntaje."""

        level = self.classify(model)

        if level is not None:
            return level

        benchmark = self.user_benchmark(model)

        return self.level_from_benchmark(benchmark.score) if benchmark else None

    def check(
        self,
        model: Optional[str],
        user_level: Optional[int],
        minimum_text: Optional[str],
        recommended_text: Optional[str],
        minimum_level: Optional[int],
        recommended_level: Optional[int],
    ) -> dict:
        user_benchmark = self.user_benchmark(model)
        minimum = _required_reference(self.benchmarks, minimum_text)
        recommended = _required_reference(self.benchmarks, recommended_text)

        # Por benchmark solo si el componente del usuario y el del requisito
        # mínimo están en el catálogo; si no, por niveles aproximados.
        # Los puntajes se usan para decidir, pero no salen en la respuesta:
        # solo el veredicto y los nombres de los modelos comparados.
        if user_benchmark and minimum:
            return {
                "component": self.name,
                "basis": "benchmark",
                "level": _level(
                    user_benchmark.score,
                    minimum.score,
                    recommended.score if recommended else None,
                ),
                "yours": None,
                "minimum": None,
                "recommended": None,
                "yours_name": user_benchmark.name,
                "minimum_name": minimum.name,
                "recommended_name": recommended.name if recommended else None,
                "unit": None,
            }

        return {
            "component": self.name,
            "basis": "level",
            "level": _level(user_level, minimum_level, recommended_level),
            "yours": user_level,
            "minimum": minimum_level,
            "recommended": recommended_level,
            "unit": "nivel",
        }

    def source_if_used(self, check: dict) -> Optional[dict]:
        if check["basis"] != "benchmark":
            return None

        return self.benchmarks.describe_source()


class EstimateCompatibility:
    def __init__(
        self,
        requirements_repository: GameRequirementsRepository,
        gpu_benchmarks: Optional[HardwareBenchmarkRepository] = None,
        cpu_benchmarks: Optional[HardwareBenchmarkRepository] = None,
    ):
        self.requirements_repository = requirements_repository

        self._gpu = _Component("gpu", gpu_benchmarks, classify_gpu, level_from_score)
        self._cpu = _Component("cpu", cpu_benchmarks, classify_cpu, cpu_level_from_score)

    def execute(
        self,
        game_id: int,
        ram_gb: int,
        gpu_score: int,
        storage_gb: Optional[int] = None,
        gpu_name: Optional[str] = None,
        cpu_name: Optional[str] = None,
        cpu_score: Optional[int] = None,
    ) -> dict:
        requirements = self.requirements_repository.get_by_game_id(game_id)

        if requirements is None:
            return {
                "game_id": game_id,
                "status": "Requisitos no disponibles",
            }

        # Si el usuario indicó el modelo y se reconoce, ese nivel prevalece
        # sobre el número enviado.
        recognized_gpu_score = self._gpu.recognized_level(gpu_name)
        user_gpu_score = recognized_gpu_score or gpu_score

        recognized_cpu_score = self._cpu.recognized_level(cpu_name)
        user_cpu_score = recognized_cpu_score or cpu_score

        gpu_check = self._gpu.check(
            gpu_name,
            user_gpu_score,
            requirements.minimum_details.get("graphics"),
            requirements.recommended_details.get("graphics"),
            requirements.minimum_gpu_score,
            requirements.recommended_gpu_score,
        )

        cpu_check = self._cpu.check(
            cpu_name,
            user_cpu_score,
            requirements.minimum_details.get("processor"),
            requirements.recommended_details.get("processor"),
            requirements.minimum_cpu_score,
            requirements.recommended_cpu_score,
        )

        checks = [
            {
                "component": "ram",
                "level": _level(
                    ram_gb,
                    requirements.minimum_ram_gb,
                    requirements.recommended_ram_gb,
                ),
                "yours": ram_gb,
                "minimum": requirements.minimum_ram_gb,
                "recommended": requirements.recommended_ram_gb,
                "unit": "GB",
            },
            cpu_check,
            gpu_check,
            {
                "component": "storage",
                "level": _level(
                    storage_gb,
                    requirements.minimum_storage_gb,
                    requirements.minimum_storage_gb,
                ),
                "yours": storage_gb,
                "minimum": requirements.minimum_storage_gb,
                "recommended": requirements.recommended_storage_gb,
                "unit": "GB",
            },
        ]

        compared_levels = [
            check["level"]
            for check in checks
            if check["level"] != UNKNOWN
        ]

        if INSUFFICIENT in compared_levels:
            status = "No compatible"
        elif all(level == RECOMMENDED for level in compared_levels):
            status = "Compatible"
        else:
            status = "Compatible con limitaciones"

        return {
            "game_id": game_id,
            "status": status,
            "minimum_ram_gb": requirements.minimum_ram_gb,
            "recommended_ram_gb": requirements.recommended_ram_gb,
            "minimum_gpu_score": requirements.minimum_gpu_score,
            "recommended_gpu_score": requirements.recommended_gpu_score,
            "minimum_cpu_score": requirements.minimum_cpu_score,
            "recommended_cpu_score": requirements.recommended_cpu_score,
            "minimum_storage_gb": requirements.minimum_storage_gb,
            "recommended_storage_gb": requirements.recommended_storage_gb,
            "source": requirements.source,
            "gpu_score_used": user_gpu_score,
            "gpu_recognized": (
                None
                if not gpu_name
                else recognized_gpu_score is not None
            ),
            "gpu_benchmark": self._gpu.source_if_used(gpu_check),
            "cpu_score_used": user_cpu_score,
            "cpu_recognized": (
                None
                if not cpu_name
                else recognized_cpu_score is not None
            ),
            "cpu_benchmark": self._cpu.source_if_used(cpu_check),
            # Verdadero cuando algún componente no se pudo comparar.
            "partial": len(compared_levels) < len(checks),
            "checks": checks,
            "requirements_text": {
                "minimum": requirements.minimum_details,
                "recommended": requirements.recommended_details,
            },
        }
