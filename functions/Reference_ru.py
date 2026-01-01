""" Шаблон растровой функции ArcGIS на русском языке.

Модуль представляет собой справочную реализацию на русском языке растровой функции, 
демонстрирующую необходимые методы и атрибуты.
Может использоваться как шаблон с полными аннотациями типов и русскоязычной документацией.

Notes
-----
- Все docstring и комментарии предоставлены на русском языке
- Все классы и методы имеют подробные аннотации типов (type hints)
- Файл соответствует стандартам кодирования ArcGIS Python Raster Functions
- Включен пример использования
- Для производственного использования требуется полноценное тестирование, которое не проводилось

:Author: Grishkin Maksim<FFFFF@bk.ru>
:Created: 01.01.2026
"""

import datetime
import itertools
import math
import pathlib
from enum import unique, IntFlag, StrEnum, IntEnum
from functools import reduce
from typing import Any, NamedTuple, TypedDict, NotRequired, Literal, TypeAlias, Optional

import arcpy
import numpy as np

__all__ = ['GumbelExtreme']


# region Типизация обменных форматов с ArcGis
@unique
class _ArgFunctionDataType(StrEnum):
    """Тип данных аргумента растровой функции"""
    NUMERIC = 'numeric'
    STRING = 'string'
    RASTER = 'raster'
    RASTERS = 'rasters'
    BOOLEAN = 'boolean'


class _InvalidateProperty(IntFlag):
    """Битовая маска (OR), указывающая, какие свойства родительского набора данных должны игнорироваться.
    
    Attributes
    ----------
    NONE
        Никакие свойства не должны игнорироваться.
    XFORM 
        XForm
    STATISTICS 
        Статистика
    HISTOGRAM 
        Гистограмма
    KEY_PROPERTIES 
        Ключевые свойства
    ALL
        Все свойства игнорируются
    """
    NONE = 0
    XFORM = 1
    STATISTICS = 2
    HISTOGRAM = 4
    KEY_PROPERTIES = 8
    ALL = XFORM | STATISTICS | HISTOGRAM | KEY_PROPERTIES


class _InheritProperty(IntFlag):
    """Битовая маска (OR), указывающая, какие свойства входного растра наследуются выходным растром.
    
    Attributes
    ----------
    NONE
        Никакие свойства не наследуются
    PIXEL_TYPE
        Тип данных пикселя (Pixel type),
    NO_DATA
        Значение NoData,
    DIMENSIONS
        Размеры (система координат, экстент, размер пикселя),
    RESAMPLING
        Способ изменения разрешения.
    ALL
        Все свойства наследуются
    """

    NONE = 0
    PIXEL_TYPE = 1
    NO_DATA = 2
    DIMENSIONS = 4
    RESAMPLING = 8
    ALL = PIXEL_TYPE | NO_DATA | DIMENSIONS | RESAMPLING


class _ResamplingType(IntEnum):
    """Метод изменения разрешения, применяемый к выходным пикселям"""
    NEAREST_NEIGHBOR = 0
    BILINEAR_INTERPOLATION = 1
    CUBIC_CONVOLUTION = 2
    MAJORITY = 3
    BILINEAR_INTERPOLATION_PLUS = 4
    BILINEAR_GAUSSIAN_BLUR = 5
    BILINEAR_GAUSSIAN_BLUR_PLUS = 6
    AVERAGE = 7
    MINIMUM = 8
    MAXIMUM = 9
    VECTOR_AVERAGE = 10


@unique
class _PixelType(StrEnum):
    """ Тип значения в пикселях растра
    
    `Описание <https://numpy.org/doc/stable/reference/arrays.interface.html>`_.
    """
    T1 = 't1'
    T2 = 't2'
    T4 = 't4'
    I1 = 'i1'
    I2 = 'i2'
    I4 = 'i4'
    U1 = 'u1'
    U2 = 'u2'
    U4 = 'u4'
    F4 = 'f4'
    F8 = 'f8'


class _ExtentTuple(NamedTuple):
    """ Вспомогательный кортеж для экстента растра """
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def to_arcPy_Polygon(self, spatial_reference: arcpy.SpatialReference) -> arcpy.Polygon:
        array = arcpy.Array([arcpy.Point(self.x_min, self.y_min),
                             arcpy.Point(self.x_min, self.y_max),
                             arcpy.Point(self.x_max, self.y_max),
                             arcpy.Point(self.x_max, self.y_min)])

        return arcpy.Polygon(array, spatial_reference=spatial_reference)


Extent: TypeAlias = _ExtentTuple | tuple[float, float, float, float]


class _ParameterInfo(TypedDict):
    """ Описание аргумента растровой функции
    
    Attributes
    ----------
    name
        Ключ словаря для обращения к значения параметра в других методах
    dataType
        Тип данных
    value : default=None
        Значение по умолчанию для аргумента или `None`, если отсутствует
    required : default=False
        Обязательный аргумент или нет (True/False)
    displayName : default=name
        Отображаемое имя в UI
    domain : default=None
         Множество допустимых значений (только для dataType == 'string'),
         например, {'Minimum', 'Maximum', 'Mean'}
    description
        Детальное описание параметра, отображаемое в подсказке UI    
    """
    name: str
    dataType: _ArgFunctionDataType
    value: NotRequired[Any]
    required: NotRequired[bool]
    displayName: NotRequired[str]
    domain: NotRequired[set[str]]
    description: str


class _ConfigCreateRasterInfo(TypedDict):
    """ Конфигурация создания растра

    Attributes
    ----------
    extractBands
        Индексы каналов входного растра, которые необходимо извлечь и передать в `updatePixels()`.
        Если не определено, то доступны все каналы.
        Индекс начинается с 0.
    compositeRasters : default=False
        Флаг объединения всех входных растров в один многоканальный растр.
        Если True, растр с именем 'compositeRasters' доступен в `updateRasterInfo()` и `updatePixels()`.
    inheritProperties : default: _InheritProperty.ALL
        Битовая маска (OR), указывающая, какие свойства входного растра наследуются выходным растром.
    invalidateProperties : int, default: _InvalidateProperty.NONE
        Битовая маска (OR), указывающая, какие свойства родительского набора данных должны игнорироваться.
    padding : int, default=0
        Количество дополнительных пикселей, добавляемых с каждой стороны входного изображения.
    CropSizeFixed : {0, 1}, default=1
        Способ обрезки тайлов вокруг объекта в emd-файле:
            0 : Переменный размер тайла для точного соответствия размерам объекта,
            1 : Фиксированный размер тайла, даже если остаётся пустое пространство.
    BlackenAroundFeature : {0, 1}, default=1
        Определяет, нужно ли закрашивать черным цветом пиксели вне объекта в каждом изображении-тайле:
            0 : Не закрашивать, оставить как есть,
            1 : Закрашивать пиксели вне объекта черным цветом.
    supportsBandSelection : default=False
        Активирует возможность применения функции только к выбранному / видимому каналу.
    inputMask : default=False
        Флаг необходимости передать в аргумент pixelBlocks метода `updatePixels()` массив маски NoData
        для всех входных растров.
        Если False, то для повышения производительности маски не предоставляются.
    resamplingType : default=0
        Определяет метод изменения разрешения, применяемый к выходным пикселям.
    """
    extractBands: NotRequired[tuple[int, ...]]
    compositeRasters: NotRequired[bool]
    inheritProperties: NotRequired[_InheritProperty]
    invalidateProperties: NotRequired[_InvalidateProperty]
    padding: NotRequired[int]
    CropSizeFixed: NotRequired[Literal[0, 1]]
    BlackenAroundFeature: NotRequired[Literal[0, 1]]
    supportsBandSelection: NotRequired[bool]
    inputMask: NotRequired[bool]
    resamplingType: NotRequired[_ResamplingType]


class _RasterStatistics(TypedDict):
    """ Статистика растра

    Attributes
    ----------
    minimum
        Приблизительно минимальное значение
    maximum
        Приблизительно максимальное значение
    mean
        Приблизительно среднее значение
    standardDeviation
        Приблизительно стандартное отклонение
    skipFactorX
        Шаг выборки по горизонтали при расчете статистики
    skipFactorY
        Шаг выборки по вертикали при расчете статистики
    """
    minimum: float
    maximum: float
    mean: float
    standardDeviation: float
    skipFactorX: int
    skipFactorY: int


class _RasterHistogramX(TypedDict):
    """ Параметры гистограммы растра

    Attributes
    ----------
    minimum
        Минимальное значение
    maximum
        Максимальное значение
    size
        Количество бинов
    """
    minimum: float
    maximum: float
    size: int


class _BlockPixelsInfo(TypedDict):
    """ Описание выходного растра, из которого выбран блок пикселей
    
    Attributes
    ----------
    extent
        Экстент в координатах карты (XMin, YMin, XMax, YMax)
    pixelType
        Тип пикселя (`описание <https://numpy.org/doc/stable/reference/arrays.interface.html>`_).
    spatialReference
        EPSG-код системы координат карты
    cellSize
        Размер ячейки по X и Y
    width
        Количество столбцов в выходном растре
    height
        Количество строк в выходном растре
    noData
        Массив значений NoData для каждого канала (длина — количество каналов)
    multidimensionalDefinition 
        Определение среза выходного растра.
        Пример: `({'variableName': 'water_temp', 'dimensionName': 'StdZ', 'isSlice': False, 'values': (minZVal, maxZVal)}, {'variableName': 'water_temp', 'dimensionName': 'StdTime', 'isSlice': False, 'values': (minTVal, maxTVal)})`
    """
    extent: Extent
    pixelType: _PixelType | str
    spatialReference: int
    cellSize: tuple[float, float]
    width: int
    height: int
    noData: tuple[int | float, ...] | None
    multidimensionalDefinition: NotRequired[tuple[dict, ...]]


class _RasterInfo(TypedDict):
    """ Описание растра (входного или выходного)

    Attributes
    ----------
    bandCount
        Количество каналов в растре
    pixelType
        Тип пикселя (`описание <https://numpy.org/doc/stable/reference/arrays.interface.html>`_).
    noData
        Массив значений NoData для каждого канала (длина — количество каналов)
    cellSize
        Размер ячейки по X и Y
    nativeExtent
        Экстент в координатах изображения (XMin, YMin, XMax, YMax)
    nativeSpatialReference
        EPSG-код системы координат изображения
    geodataXform
        XML-строка преобразования между системой координат изображения и карты
    extent
        Экстент в координатах карты (XMin, YMin, XMax, YMax)
    spatialReference
        EPSG-код системы координат карты
    colormap
        Кортеж из четырех массивов для цветовой карты:
            - `colormap[0]` - значения пикселей в индексируемом растре (int32);
            - `colormap[1]` - красная компонента RGB (uint8);
            - `colormap[2]` - зеленая компонента RGB (uint8);
            - `colormap[3]` - синяя компонента RGB (uint8).
    rasterAttributeTable
        Путь к таблице атрибутов и кортеж связанных с ним имен полей.
        Для доступа к таблице атрибутов используйте функцию `arcpy.da.TableToNumPyArray()`
    levelOfDetails
        Количество уровней детализации (пирамид) в растре
    origin
        Координаты начала координат (x, y)
    resampling default=False
        По документации — resampling, по факту приходит Resampling.
        Способна ли растровая функция Python обрабатывать пиксели, разрешение которых было изменено при запросе:
            - Если False, то `updatePixels` получает на обработку блок пикселей в исходном (native) разрешении
              (или в разрешении ближайшего слоя пирамиды), а результат обработки передескретизируется ArcGIS
              под разрешение запроса.
            - Если True, то `updatePixels` получает на обработку блок пикселей в целевом разрешении.
        Разрешение блока пикселей доступно в методах `selectRasters` и `updatePixels` через свойство `cellSize`
    histogram
        Кортеж гистограмм для каждого канала (длина — количество каналов)
    histogramX
        Кортеж гистограмм для каждого канала (длина — количество каналов).
    statistics
        Кортеж статистик для каждого канала (длина — количество каналов).
    bandSelection
        Флаг выбора канала
    blockHeight
        Высота блока пикселей (не документировано)
    blockWidth
        Ширина блока пикселей (не документировано)
    firstPyramidLevel
        Первый уровень пирамиды (не документировано)
    maxPyramidLevel
        Максимальный уровень пирамиды (не документировано)
    format
        Формат растра, например TIFF (не документировано)
    
    Notes
    -----
    1. Кортежи `cellSize` и `maximumCellSize` можно использовать для создания объекта `arcpy.Point`.
    2. Кортежи `extent`, `nativeExtent` и `origin` можно использовать для создания объекта `arcpy.Extent`.
    3. EPSG-коды `nativeSpatialReference` и `spatialReference`
       можно использовать для создания объекта `arcpy.SpatialReference()`.
    """
    bandCount: int
    pixelType: _PixelType | str
    noData: Optional[np.ndarray]
    cellSize: tuple[float, float]
    nativeExtent: Extent
    nativeSpatialReference: int
    geodataXform: NotRequired[str]
    extent: Extent
    spatialReference: int
    colormap: NotRequired[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]
    rasterAttributeTable: NotRequired[tuple[str, tuple[str, ...]]]
    levelOfDetails: int
    origin: tuple[float, float]
    resampling: NotRequired[bool]  # По документации — resampling, по факту приходит Resampling 
    histogram: tuple[np.ndarray, ...]
    histogramX: tuple[_RasterHistogramX, ...]
    statistics: tuple[_RasterStatistics, ...]
    bandSelection: NotRequired[bool]
    blockHeight: NotRequired[int]
    blockWidth: NotRequired[int]
    firstPyramidLevel: NotRequired[int]
    maxPyramidLevel: NotRequired[int]
    format: NotRequired[str]


class _ProductInfo(TypedDict):
    """Словарь с информацией о продукте ArcGis для проверки лицензирования.
    
    Attributes
    ----------
    productName
        Название продукта ArcGIS.
    version
        Строка версии продукта.
    path
        Путь установки продукта.
    major
        Номер версии основной.
    minor
        Номер версии дополнительный.
    build
        Номер сборки.
    spNumber
        Номер сервис-пака.
    spBuild
        Сборка сервис-пака.
    
    """

    productName: Literal['Desktop', 'Server', 'Engine', 'ArcGISPro']
    version: str
    path: str
    major: int
    minor: float
    build: int
    spNumber: NotRequired[int]
    spBuild: NotRequired[int]


class _LicenseCheckResult(TypedDict):
    """ Результат проверки лицензирования растровой функции.
    
    Attributes
    ----------
    okToRun
        Есть ли разрешение на выполнение функции (True/False).
    message
        Сообщение при отказе в лицензии (`okToRun==False`).
    productLevel : str
        Требуемый уровень лицензии продукта.
    extension : str
        Требуемое расширение ArcGis.
    """
    okToRun: bool
    message: NotRequired[str]
    productLevel: NotRequired[Literal['Basic', 'Standard', 'Advanced']]
    extension: NotRequired[str]


# endregion

class GumbelExtreme:
    """ Растровая функция ArcGis

    Конвейер вызова методов в ArcGis:
    -----
    `isLicensed`
        проверяет наличие лицензии на выполнение растровой функции
    `getParameterInfo`
        предоставляет ArcGis информацию об аргументах, необходимых для запуска растровой ф-ции.
    `getConfiguration`
        на основе скалярных аргументов отдает ArcGis ожидаемый формат информации о входных растрах
        и предварительные настройки создания выходного растра.
    `updateRasterInfo`
        получает от ArcGis предварительное описание выходного растра `'output_info'`, и отдает его уточненное описание.
    `selectRasters`
        позволяет выбрать подмножество входных растров, из которых пиксели передаются в `updatePixels`.
    `updatePixels`
        получает от ArcGis блок пикселей входных изображений и возвращает их обработанные значения.
    `updateKeyMetadata`
        Определяет метаданные для выходного растра и отдельных каналов

    Attributes
    ----------
    debug : bool
        Флаг включения режима отладки (логирования).
    name : str
        Имя растровой функции.
    description : str
        Описание растровой функции.

    mean_name : str
        Имя параметра для растра среднего значения.
    std_name : str
        Имя параметра для растра стандартного отклонения.
    ari_name : str
        Имя параметра для периода повторяемости (ARI).
    ari : float
        Значение периода повторяемости (ARI).
    """

    def __init__(self):
        self.debug = False
        self.name = "Gumbel Extreme Function"
        self.description = ("Расчет уровня экстремальной (max/min) интенсивности явления с периодом повторяемости "
                            "ARI лет (Average Recurrence Interval) по распределению Гумбеля.\n"
                            "Пример: расчет максимальных дневных осадков, которые будут достигнуты за 5 лет.\n"
                            "Формула: x = μ - β·ln(-ln(1 - 1 ÷ ARI)), где\n"
                            "x — расчетная интенсивность экстремального явления с периодом повторяемости ARI\n"
                            "ARI — средний период повторяемости достижения экстремальным явлением указанной величины\n"
                            "μ и β будут вычислены методом моментов на основании на основании среднего выборки (x̄) "
                            "и стандартного отклонения выборки (s)")

        self.mean_name = 'mean'
        self.std_name = 'std'
        self.ari_name = 'ari'

        self.ari = 1.

    def write_debug(self, msg: str):
        """ Записывает отладочное сообщение

        Если включен режим отладки `self.debug == True`, то записывает отладочное сообщение

        :param msg: Сообщение отладки
        """
        if self.debug:
            log(msg)

    def set_params(self, params: dict[str, float | str | dict | tuple[dict, ...] | bool]) -> dict[str, Any]:
        """Сохраняет переданные параметры обработки растра

        Данный метод выделен из `updateRasterInfo`, чтобы не смешивать ответственность

        Parameters
        ----------
        params
            Словарь параметров, указанных пользователем и информация о растрах.
            Подробное описание смотри в методе `updateRasterInfo`

        Returns
        -------
        dict
            Входящий параметр `params`.
        """

        self.ari = params[self.ari_name]

        return params

    def getParameterInfo(self) -> list[_ParameterInfo]:
        """Отдаёт информацию обо всех аргументах растровой функции, для их отражения в UI.

        Returns
        -------
        list[_ParameterInfo]
            Список словарей с описанием аргументов растровой функции
        """

        self.write_debug(f"Вызвана {self.getParameterInfo.__name__}")

        return [
            _ParameterInfo(
                name=self.mean_name,
                dataType=_ArgFunctionDataType.RASTER,
                value=None,
                required=True,
                displayName="Растр среднего",
                description="Одноканальный растр, в котором пиксели — это среднее экстремальной величины (max/min)"
            ),
            _ParameterInfo(
                name=self.std_name,
                dataType=_ArgFunctionDataType.RASTER,
                value=None,
                required=True,
                displayName="Растр стандартного отклонения",
                description="Одноканальный растр, в котором пиксели — это СКО экстремальной величины (max/min)"
            ),
            _ParameterInfo(
                name=self.ari_name,
                dataType=_ArgFunctionDataType.NUMERIC,
                value=20,
                required=True,
                displayName="Период повторяемости (ARI)",
                description="Период в годах (например, 5)"
            )
        ]

    def getConfiguration(self, **scalars) -> _ConfigCreateRasterInfo:
        """ Отдает формат получения сведений о входящих растрах + предварительную конфигурацию выходного растра.

        Определяет:
            - формат передачи следующим функциям в конвейере информации о входных растрах
            - способ Формирует предварительное описание конфигурации выходного растра, базирующееся только на скалярных
              параметрах.

        Конфигурация выходного растра потом может быть уточнена в функции `updateRasterInfo` на основании
        информации о входных растрах.

        Parameters
        ----------
        **scalars
            Словарь скалярных параметров, где scalars['arg_name'] возвращает значение,
            указанное пользователем для аргумента с именем 'arg_name' в `getParameterInfo()`.

        Returns
        -------
        _ConfigCreateRasterInfo
            Словарь с конфигурацией создания растра

        """

        self.write_debug(f"Вызвана {self.getConfiguration.__name__}")
        self.write_debug(f"{scalars=}")

        return _ConfigCreateRasterInfo(
            invalidateProperties=_InvalidateProperty.STATISTICS | _InvalidateProperty.HISTOGRAM | _InvalidateProperty.KEY_PROPERTIES,
            supportsBandSelection=True,  # поддержка выбора канала растра
            inputMask=False  # унаследуем NoData
        )

    def updateRasterInfo(self, **kwargs) -> dict[Literal['output_info'], _RasterInfo]:
        """Обновляет и дополняет предварительно настроенную конфигурацию выходного растра
        
        Этот метод вызывается после `getConfiguration` и при каждой инициализации
        растрового набора данных, содержащего данную Python-функцию.
        Позволяет динамически изменять свойства выходного растра.

        Словарь `kwargs` содержит следующие данные:
            `kwargs['arg_name']` : Any
                значение, указанное пользователем для аргумента с именем 'arg_name' в `getParameterInfo()`,
            `kwargs['rasterName_info']` : _RasterInfo or tuple of _RasterInfo
                информация о входном растре/растрах для аргумента с именем 'rasterName' в `getParameterInfo()`:
                    * для типа аргумента 'raster' — словарь с информацией о растре
                    * для типа аргумента 'rasters' — кортеж словарей с информацией о растре
            `kwargs['output_info']` : _RasterInfo
                информация о выходном растре, основанная на `getConfiguration()` и первом растре
        
        Parameters
        ----------
        **kwargs
            Словарь скалярных параметров и информации о растрах: вх и вых.

        Returns
        -------
        dict[str, _RasterInfo]
            Входящий словарь с обновленной информацией о выходном растре `kwargs['output_info']`.

        """
        self.write_debug(f"Вызвана {self.updateRasterInfo.__name__}")
        self.write_debug(f"{kwargs=}")

        self.set_params(kwargs)

        out_raster: _RasterInfo = kwargs['output_info']

        # Переопределение настроек выходного растра
        out_raster['bandCount'] = 1  # Одноканальный растр
        out_raster['pixelType'] = _PixelType.F4  # Тип ячейки растра — float
        out_raster['statistics'] = ()  # Неизвестна статистика выходного растра
        out_raster['histogram'] = ()  # Неизвестна гистограмма выходного растра
        out_raster['histogramX'] = ()  # Неизвестна гистограмма выходного растра
        out_raster['resampling'] = True  # Можно получать ячейки с измененным разрешением

        in_rasters = (kwargs[f"{self.mean_name}_info"], kwargs[f"{self.std_name}_info"])

        return {'output_info': self.update_mosaic_extent(out_raster, in_rasters)}

    def update_mosaic_extent(self, out_raster: _RasterInfo,
                             in_rasters: tuple[_RasterInfo | tuple[_RasterInfo, ...], ...]) -> _RasterInfo:
        """ Обновляет экстент выходного растра, как объединенный экстент входных растров

        Если на вход передан список растров (например, набор данных мозаики) с разным экстентом, то эта ф-ция
        позволяет присвоить выходному растру объединенный экстент

        Parameters
        ----------
        out_raster
            Информация о выходном растре.
        in_rasters
            Входные растры.

        Returns
        -------
        _RasterInfo
            Словарь с обновленной информацией о выходном растре.
        """

        rasters_tuples = [item if isinstance(item, tuple) else (item,) for item in in_rasters]
        flatten: list[_RasterInfo] = list(itertools.chain.from_iterable(rasters_tuples))

        self.write_debug(f"Вызвана {self.update_mosaic_extent.__name__}")
        if len(flatten) == 1:
            self.write_debug(f"На входе один растр. Ничего делать не требуется")
            return out_raster

        # Объединение экстентов растров        
        extents = [_ExtentTuple(*raster_info['nativeExtent']) for raster_info in flatten]
        self.write_debug(f"Входящие экстенты {extents}")

        srss = [arcpy.SpatialReference(raster_info['nativeSpatialReference']) for raster_info in flatten]
        extents_pgn = [e[0].to_arcPy_Polygon(e[1]) for e in zip(extents, srss)]
        srs_target = arcpy.SpatialReference(out_raster['spatialReference'])
        extents_pgn_proj: list[arcpy.Geometry] = [e.projectAs(srs_target) for e in extents_pgn]
        extent_combined = reduce(lambda a, b: a | b, extents_pgn_proj)

        # Уточнение границ экстента с учетом разрешения
        dx = out_raster['cellSize'][0]
        dy = out_raster['cellSize'][1]

        x_min = extent_combined.extent.XMin
        y_min = extent_combined.extent.YMin
        x_max = extent_combined.extent.XMax
        y_max = extent_combined.extent.YMax

        cols = math.ceil((x_max - x_min) / dx)
        rows = math.ceil((y_max - y_min) / dy)
        y_min = y_max - (rows * dy)
        x_max = x_min + (cols * dx)
        out_ext = _ExtentTuple(x_min, y_min, x_max, y_max)

        out_raster['extent'] = out_ext
        out_raster['nativeExtent'] = out_ext
        out_raster['nativeSpatialReference'] = out_raster['spatialReference']
        self.write_debug(f"Выходной экстент {out_ext}")

        return out_raster

    # Странный метод, вызовы его не наблюдаются в логе
    # def selectRasters(self, tlc: tuple[float, float], shape: tuple[int, int] | tuple[int, int, int],
    #                   props: _BlockPixelsInfo) -> tuple:
    #     """ Определяет подмножество входных растров, из которых пиксели передаются в `updatePixels`
    # 
    #     Parameters
    #     ----------
    #     tlc : tuple of 2 floats
    #         Координаты верхнего левого угла блока пикселей.
    #     shape : tuple of ints
    #         Размер блока пикселей в виде кортежа:
    #             - для одноканального растра: (кол-во строк/высота, кол-во колонок/ширина);
    #             - для многоканального растра: (канал, кол-во строк/высота, кол-во колонок/ширина).
    #         Выходные массивы пикселей и маски должны соответствовать этой форме.
    #     props : _BlockPixelsInfo
    #         Словарь со свойствами выходного растра, для которого запрашивается блок пикселей.
    #         
    #     Returns
    #     -------
    #     tuple
    #     
    #     
    #     """
    # 
    #     self.write_debug(f"Вызвана {self.selectRasters.__name__}")
    #     self.write_debug(f"{tlc=}")
    #     self.write_debug(f"{shape=}")
    #     self.write_debug(f"{props=}")
    # 
    #     return ()

    def updatePixels(self, tlc: tuple[float, float], shape: tuple[int, int] | tuple[int, int, int],
                     props: _BlockPixelsInfo, **pixelBlocks: np.ndarray | tuple[np.ndarray, ...]) -> dict[
        Literal['output_pixels', 'output_mask'], np.ndarray]:
        """
        Формирует выходные пиксели на основе блоков пикселей всех входных растров.
        
        Parameters
        ----------
        tlc : tuple of 2 floats
            Координаты верхнего левого угла блока пикселей.
        shape : tuple of ints
            Размер блока пикселей в виде кортежа:
                - для одноканального растра: (кол-во строк/высота, кол-во колонок/ширина);
                - для многоканального растра: (канал, кол-во строк/высота, кол-во колонок/ширина).
            Выходные массивы пикселей и маски должны соответствовать этой форме.
        props : _BlockPixelsInfo
            Словарь со свойствами выходного растра, для которого запрашивается блок пикселей.
        pixelBlocks :
            Пиксели и маска, ассоциированные с каждым входным растром.
            Ключ словаря `pixelBlocks` для аргумента с именем 'name': 'name_pixels' и 'name_mask'.
            Тип значения для аргументов типа 'raster' — ndarrays, для 'rasters' — (ndarrays,).

        Returns
        -------
        dict[str, np.ndarray]
            Словарь с обязательным ключом 'output_pixels' и опциональным 'output_mask'. 
            'output_pixels' : numpy.ndarray
                Выходные значения пикселей. Тип данных должен соответствовать props['pixelType']
            'output_mask' : numpy.ndarray, optional
                Маска выходных пикселей. Тип данных: uint8 (u1)

        Notes
        ----------
            - Этот метод вызывается для генерации выходных пикселей «на лету».
            - Может обрабатывать не всё изображение, а отдельный его блок.
            - Для корректной работы все выходные массивы должны быть непрерывными (c-contiguous).
            - Скалярные параметры доступны только в методах `getConfiguration` или `updateRasterInfo`.
            - Размер массивов должен точно соответствовать параметру `shape`.
            - Растровая функция, не предназначенная для изменения пикселей, может не определять этот метод.
        """
        self.write_debug(f"Вызвана {self.updatePixels.__name__}")
        self.write_debug(f"{tlc=}")
        self.write_debug(f"{shape=}")
        self.write_debug(f"{props=}")
        self.write_debug(f"{pixelBlocks=}")

        mean = np.array(pixelBlocks[f"{self.mean_name}_pixels"], copy=False)
        std = np.array(pixelBlocks[f"{self.std_name}_pixels"], copy=False)
        result = calc_gumbel_value(self.ari, mean, std).astype(props['pixelType'], copy=False)

        return {'output_pixels': result}

    def updateKeyMetadata(self, names: tuple[str, ...], bandIndex: int, **keyMetadata: Any | None) -> dict[
        str, Any | None]:
        """ Определяет метаданные для выходного растра и отдельных каналов.
                
        Parameters
        ----------
        names
            Названия запрошенных метаданных.
            Пустой кортеж указывает на запрос всех доступных свойств.
        bandIndex
            Индекс канала (band), для которого запрашиваются метаданные.
            Индексация начинается с 0.
            Значение -1 указывает на запрос метаданных всего растра.
        **keyMetadata : dict
            Ключевые аргументы, содержащие известные метаданные (или их подмножество, определяемое кортежем `names`).
            Названия метаданных соответствуют ключам словаря.
        
        Returns
        -------
        dict[str, Any | None]
            Обновленный словарь ключевых метаданных.
            Должен содержать все переданные в `keyMetadata` ключи с обновленными
            значениями, а также может содержать новые ключи.
        
        Notes
        -----
        - Метод вызывается при запросе метаданных от растровой функции
        - Может использоваться для динамического вычисления метаданных
        - Позволяет переопределять стандартные значения метаданных
        """
        self.write_debug(f"Вызвана {self.updateKeyMetadata.__name__}")
        self.write_debug(f"{names=}")
        self.write_debug(f"{bandIndex=}")
        self.write_debug(f"{keyMetadata=}")

        if bandIndex == -1:  # уровень всего растра
            keyMetadata['datatype'] = 'Scientific'
        else:                # уровень канала растра
            keyMetadata['wavelengthmin'] = None
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = f'ari_{self.ari}'
        return keyMetadata

    def isLicensed(self, **productInfo: _ProductInfo) -> _LicenseCheckResult:
        """ Проверяет лицензионную возможность выполнения растровой функции.
        
        Метод вызывается сразу после создания объекта функции и позволяет
        проверить наличие необходимых лицензий и совместимость версий продукта.
        
        Parameters
        ----------
        **productInfo
            Информация о продукте и среде выполнения.
            Передается как именованные аргументы с ключами
        
        Returns
        -------
        _LicenseCheckResult
            Словарь с результатом проверки лицензирования.
        
        Notes
        -----
        - Метод вызывается автоматически при создании растровой функции.
        - При `okToRun==False` выполнение функции будет заблокировано.
        - Проверка версий продукта выполняется на основе полей major, minor, build.
        """
        self.write_debug(f"Вызвана {self.isLicensed.__name__}")
        self.write_debug(f"{productInfo=}")

        return _LicenseCheckResult(okToRun=True)


# region Вспомогательные функции
def calc_gumbel_value(ari: float, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """ Вычисляет интенсивность явления, описываемого по распределению Гумбеля.

        Формула расчета:
            x = μ - β·ln(-ln(1 - 1÷ARI))
        где:
            - X — экстремальная интенсивность,
            - μ, β — коэффициенты, вычисляемые на основании среднего (x̄) и стандартного отклонения выборки (s),
            - ARI — период повторяемости (Average Return Interval).

        Parameters
        ----------
        ari
            Период повторяемости, лет
        mean
            Массив средних значений выборки
        std
            Массив стандартных отклонений выборки

        Returns
        -------
        np.ndarray
            Расчетные интенсивности X для заданного периода ari
        """

    if ari == 1.:
        return mean

    # np.euler_gamma может быть недоступна в старых версиях numpy
    euler_gamma = getattr(np, 'euler_gamma', 0.5772156649015329)

    beta = std * np.sqrt(6) / np.pi
    mu = mean - (euler_gamma * beta)
    return mu - beta * np.log(-np.log(1 - 1 / ari))


def log(msg: str, incl_timestamp: bool = True) -> None:
    """ Записывает сообщение в лог-файл с возможностью добавления временной метки.

    Parameters
    ----------
    msg
        Текст сообщения для логирования.
    
    incl_timestamp
        Если True — добавляет временную метку к сообщению.

    Notes
    -----
    - Лог-файл создается в той же директории, что и текущий модуль
    - Имя файла: `<имя_модуля>.log`
    - Сообщения добавляются в конец файла
    """
    log_file = pathlib.Path(__file__).with_suffix('.log')

    if incl_timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_formatted = f"[{timestamp}] {msg}\n"
    else:
        msg_formatted = f"{msg}\n"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(msg_formatted)

# endregion
