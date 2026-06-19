"""
OCR движок на базе Tesseract и EasyOCR
Извлекает текст из изображений скриншотов с улучшенной предобработкой,
адаптивным выбором режима PSM, метриками качества и кэшированием.
"""
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Результат OCR с метриками качества для мониторинга и A/B-тестов."""

    text: str
    engine: str
    duration_ms: float
    char_count: int
    token_count: int
    image_type: str
    psm_mode: int
    image_width: int
    image_height: int
    confidence: float = 0.0
    blocks_total: int = 0
    blocks_above_threshold: int = 0
    avg_confidence: Optional[float] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    high_conf_count: int = 0
    min_confidence_threshold: Optional[float] = None
    quality_flags: List[str] = field(default_factory=list)
    cache_hit: bool = False
    cache_key: Optional[str] = None

    def metrics_dict(self) -> Dict[str, Any]:
        """Возвращает метрики в JSON-совместимом виде."""
        return asdict(self)


class OCREngine:
    """Движок оптического распознавания символов с улучшенным предобработанием."""

    # PSM режимы для разных типов скриншотов
    PSM_MODES = {
        'auto': 3,           # Полный авто-режим (по умолчанию)
        'document': 6,       # Единый блок текста (таблицы, документы)
        'sparse': 11,        # Разрозненный текст (интерфейсы, формы)
        'raw_line': 13,      # Сырая строка (заголовки, кнопки)
        'single_line': 8,    # Единая строка текста
    }

    def __init__(self, lang: str = 'rus+eng'):
        """
        Инициализация OCR движка.

        Args:
            lang: Языки для распознавания (например, 'rus+eng').
        """
        self.lang = lang
        self.ocr_engine_type = os.getenv('OCR_ENGINE', 'TESSERACT').upper()

        # Инициализация EasyOCR если выбран
        if self.ocr_engine_type == 'EASYOCR':
            try:
                import easyocr
                self.easyocr_reader = easyocr.Reader(['ru', 'en'], gpu=False)
                logger.info("EasyOCR инициализирован (CPU mode)")
            except Exception as e:
                logger.warning(f"Ошибка инициализации EasyOCR: {e}. Используем Tesseract.")
                self.ocr_engine_type = 'TESSERACT'
                self.easyocr_reader = None
        else:
            self.easyocr_reader = None
            logger.info(f"Tesseract инициализирован с языками: {lang}")

        self.cache_enabled = self._parse_bool(os.getenv('OCR_CACHE_ENABLED', 'true'))
        self.cache_ttl_seconds = int(os.getenv('OCR_CACHE_TTL_SECONDS', '86400'))
        self.cache_max_items = int(os.getenv('OCR_CACHE_MAX_ITEMS', '1000'))
        self.cache_file = os.getenv('OCR_CACHE_FILE', '/app/storage/ocr_cache.json')
        self._ocr_cache: Dict[str, Dict[str, Any]] = {}

        if self.cache_enabled:
            self._load_cache()

        logger.info(
            "OCR cache: enabled=%s ttl=%ss max_items=%s file=%s",
            self.cache_enabled,
            self.cache_ttl_seconds,
            self.cache_max_items,
            self.cache_file,
        )
        logger.info(f"Поддерживаемые PSM режимы: {list(self.PSM_MODES.keys())}")

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Преобразует строковое значение в boolean."""
        return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    def _load_cache(self) -> None:
        """Загружает JSON-кэш OCR-результатов."""
        if not self.cache_file or not os.path.exists(self.cache_file):
            return

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                payload = json.load(f)

            if isinstance(payload, dict) and isinstance(payload.get('items'), dict):
                self._ocr_cache = payload['items']
                logger.info("OCR cache loaded: %s entries", len(self._ocr_cache))
        except Exception as e:
            logger.warning(f"Не удалось загрузить OCR cache: {e}")
            self._ocr_cache = {}

    def _save_cache(self) -> None:
        """Сохраняет JSON-кэш OCR-результатов атомарно."""
        if not self.cache_enabled or not self.cache_file:
            return

        try:
            cache_dir = os.path.dirname(os.path.abspath(self.cache_file))
            os.makedirs(cache_dir, exist_ok=True)

            payload = {
                'version': 1,
                'updated_at': time.time(),
                'items': self._ocr_cache,
            }

            tmp_path = f"{self.cache_file}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            os.replace(tmp_path, self.cache_file)
        except Exception as e:
            logger.warning(f"Не удалось сохранить OCR cache: {e}")

    def _get_cache_entry(self, cache_key: str) -> Optional[OCRResult]:
        """Возвращает результат из кэша, если он не истек."""
        entry = self._ocr_cache.get(cache_key)
        if not entry or not isinstance(entry, dict):
            return None

        created_at = float(entry.get('created_at', 0.0))
        if self.cache_ttl_seconds >= 0 and time.time() - created_at > self.cache_ttl_seconds:
            self._ocr_cache.pop(cache_key, None)
            return None

        result_data = entry.get('result')
        if not isinstance(result_data, dict):
            return None

        quality_flags = result_data.get('quality_flags', [])
        if not isinstance(quality_flags, list):
            quality_flags = []

        return OCRResult(
            text=str(result_data.get('text', '')),
            engine=str(result_data.get('engine', self.ocr_engine_type)),
            duration_ms=float(result_data.get('duration_ms', 0.0)),
            char_count=int(result_data.get('char_count', 0)),
            token_count=int(result_data.get('token_count', 0)),
            image_type=str(result_data.get('image_type', 'unknown')),
            psm_mode=int(result_data.get('psm_mode', 0)),
            image_width=int(result_data.get('image_width', 0)),
            image_height=int(result_data.get('image_height', 0)),
            confidence=float(result_data.get('confidence', 0.0)),
            blocks_total=int(result_data.get('blocks_total', 0)),
            blocks_above_threshold=int(result_data.get('blocks_above_threshold', 0)),
            avg_confidence=result_data.get('avg_confidence'),
            min_confidence=result_data.get('min_confidence'),
            max_confidence=result_data.get('max_confidence'),
            high_conf_count=int(result_data.get('high_conf_count', 0)),
            min_confidence_threshold=result_data.get('min_confidence_threshold'),
            quality_flags=[str(flag) for flag in quality_flags],
            cache_hit=True,
            cache_key=cache_key,
        )

    def _set_cache_entry(self, cache_key: str, result: OCRResult) -> None:
        """Сохраняет OCR-результат в кэш."""
        if not cache_key:
            return

        self._ocr_cache[cache_key] = {
            'created_at': time.time(),
            'result': result.metrics_dict(),
        }

        if self.cache_max_items > 0 and len(self._ocr_cache) > self.cache_max_items:
            sorted_items = sorted(
                self._ocr_cache.items(),
                key=lambda item: float(item[1].get('created_at', 0.0)),
            )
            for key, _ in sorted_items[: len(sorted_items) - self.cache_max_items]:
                self._ocr_cache.pop(key, None)

        self._save_cache()

    def _build_cache_key(self, image_path: str) -> str:
        """Создает стабильный ключ кэша по файлу и настройкам OCR."""
        stat = os.stat(image_path)
        components = [
            str(stat.st_mtime_ns),
            str(stat.st_size),
            self.ocr_engine_type,
            self.lang,
            str(self._get_easyocr_threshold()),
        ]
        raw_key = "|".join(components)
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def _get_easyocr_threshold(self) -> float:
        """Возвращает порог confidence для EasyOCR."""
        try:
            return float(os.getenv('EASYOCR_MIN_CONFIDENCE', '0.3'))
        except ValueError:
            return 0.3

    def _build_text_metrics(self, text: str) -> Dict[str, Any]:
        """Строит эвристические метрики качества текста для Tesseract."""
        cleaned = text.strip()
        char_count = len(cleaned)
        tokens = re.findall(r'[A-Za-zА-Яа-яЁё0-9]+', cleaned)
        token_count = len(tokens)

        alnum_chars = sum(1 for ch in cleaned if ch.isalnum())
        lang_chars = sum(1 for ch in cleaned if ch.isalnum() or ch.isspace())
        alpha_chars = sum(1 for ch in cleaned if ch.isalpha())
        upper_alpha_chars = sum(1 for ch in cleaned if ch.isalpha() and ch.isupper())

        alnum_ratio = alnum_chars / char_count if char_count else 0.0
        lang_ratio = lang_chars / char_count if char_count else 0.0
        upper_ratio = upper_alpha_chars / alpha_chars if alpha_chars else 0.0

        quality_flags: List[str] = []
        if char_count == 0:
            quality_flags.append('empty_text')
        if char_count > 0 and char_count < 30:
            quality_flags.append('low_text_length')
        if token_count == 0 and char_count > 0:
            quality_flags.append('no_tokens')
        if char_count > 0 and alnum_ratio < 0.6:
            quality_flags.append('low_alnum_ratio')
        if char_count > 0 and lang_ratio < 0.8:
            quality_flags.append('high_noise_ratio')
        if char_count > 50 and upper_ratio > 0.75:
            quality_flags.append('mostly_uppercase')

        if char_count == 0:
            heuristic_confidence = 0.0
        else:
            length_score = min(1.0, char_count / 300.0)
            heuristic_confidence = (
                length_score * 0.4
                + alnum_ratio * 0.3
                + lang_ratio * 0.3
            )
            heuristic_confidence -= len(quality_flags) * 0.1
            heuristic_confidence = max(0.0, min(1.0, heuristic_confidence))

        return {
            'char_count': char_count,
            'token_count': token_count,
            'alnum_ratio': round(alnum_ratio, 4),
            'lang_ratio': round(lang_ratio, 4),
            'upper_ratio': round(upper_ratio, 4),
            'heuristic_confidence': round(heuristic_confidence, 4),
            'quality_flags': quality_flags,
        }

    def _log_ocr_metrics(self, result: OCRResult) -> None:
        """Логирует ключевые метрики OCR-результата."""
        logger.info(
            "OCR metrics: engine=%s cache_hit=%s text_len=%d tokens=%d "
            "confidence=%.2f duration_ms=%.1f image_type=%s psm=%s "
            "blocks=%d/%d avg_conf=%s min_conf=%s flags=%s",
            result.engine,
            result.cache_hit,
            result.char_count,
            result.token_count,
            result.confidence,
            result.duration_ms,
            result.image_type,
            result.psm_mode,
            result.blocks_above_threshold,
            result.blocks_total,
            result.avg_confidence,
            result.min_confidence,
            ','.join(result.quality_flags) if result.quality_flags else 'none',
        )

    def _empty_result(
        self,
        image_path: str,
        engine: str,
        image_type: str = 'unknown',
        flags: Optional[List[str]] = None,
    ) -> OCRResult:
        """Создает пустой OCRResult для ошибочных случаев."""
        image_cv = cv2.imread(image_path)
        if image_cv is None:
            width = height = 0
        else:
            height, width = image_cv.shape[:2]

        return OCRResult(
            text='',
            engine=engine,
            duration_ms=0.0,
            char_count=0,
            token_count=0,
            image_type=image_type,
            psm_mode=0,
            image_width=int(width),
            image_height=int(height),
            quality_flags=flags or [],
        )

    def extract_text(self, image_path: str) -> str:
        """
        Извлекает текст из изображения с улучшенной предобработкой
        и адаптивным выбором PSM режима.

        Args:
            image_path: Путь к файлу изображения.

        Returns:
            Распознанный текст или пустая строка при ошибке.
        """
        return self.extract_text_with_metrics(image_path).text

    def extract_text_with_metrics(self, image_path: str) -> OCRResult:
        """Извлекает текст и возвращает результат вместе с метриками качества."""
        start_time = time.perf_counter()
        image_path = os.fspath(image_path)

        try:
            cache_key = self._build_cache_key(image_path) if self.cache_enabled else None
        except Exception as e:
            logger.warning(f"Не удалось создать OCR cache key для {image_path}: {e}")
            cache_key = None

        if cache_key:
            cached_result = self._get_cache_entry(cache_key)
            if cached_result:
                cached_result.duration_ms = 0.0
                cached_result.cache_hit = True
                cached_result.cache_key = cache_key
                logger.info("OCR cache hit: %s", cache_key[:16])
                self._log_ocr_metrics(cached_result)
                return cached_result

        try:
            # Чтение изображения через OpenCV
            image_cv = cv2.imread(image_path)
            if image_cv is None:
                logger.error(f"Не удалось прочитать изображение: {image_path}")
                result = self._empty_result(image_path, self.ocr_engine_type, flags=['image_read_failed'])
                return result

            logger.debug(f"Открыто изображение: {image_path} (размер: {image_cv.shape})")

            # Авто-определение типа изображения
            image_type = self.detect_image_type(image_cv)
            psm_mode = self.PSM_MODES.get(image_type, 3)
            logger.info(f"Тип изображения: {image_type}, PSM режим: {psm_mode}, Движок: {self.ocr_engine_type}")

            # Распознавание текста в зависимости от движка
            if self.ocr_engine_type == 'EASYOCR' and self.easyocr_reader:
                engine_result = self.extract_text_easyocr_with_metrics(image_cv, image_type, psm_mode)
            else:
                engine_result = self.extract_text_tesseract_with_metrics(image_cv, image_type, psm_mode)

            cleaned_text = self.clean_text(engine_result.text)
            text_metrics = self._build_text_metrics(cleaned_text)

            if engine_result.engine == 'EASYOCR':
                confidence = engine_result.avg_confidence if engine_result.avg_confidence is not None else 0.0
            else:
                confidence = text_metrics['heuristic_confidence']

            result = OCRResult(
                text=cleaned_text,
                engine=engine_result.engine,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                char_count=text_metrics['char_count'],
                token_count=text_metrics['token_count'],
                image_type=image_type,
                psm_mode=psm_mode,
                image_width=int(image_cv.shape[1]),
                image_height=int(image_cv.shape[0]),
                confidence=confidence,
                blocks_total=engine_result.blocks_total,
                blocks_above_threshold=engine_result.blocks_above_threshold,
                avg_confidence=engine_result.avg_confidence,
                min_confidence=engine_result.min_confidence,
                max_confidence=engine_result.max_confidence,
                high_conf_count=engine_result.high_conf_count,
                min_confidence_threshold=engine_result.min_confidence_threshold,
                quality_flags=text_metrics['quality_flags'],
                cache_hit=False,
                cache_key=cache_key,
            )

            if cache_key:
                self._set_cache_entry(cache_key, result)

            self._log_ocr_metrics(result)
            return result

        except Exception as e:
            logger.error(f"OCR ошибка для {image_path}: {e}", exc_info=True)
            result = self._empty_result(image_path, self.ocr_engine_type, flags=['ocr_exception'])
            return result

    def extract_text_tesseract(self, image_cv: np.ndarray, image_type: str, psm_mode: int) -> str:
        """Распознавание текста через Tesseract."""
        return self.extract_text_tesseract_with_metrics(image_cv, image_type, psm_mode).text

    def extract_text_tesseract_with_metrics(
        self,
        image_cv: np.ndarray,
        image_type: str,
        psm_mode: int,
    ) -> OCRResult:
        """Распознавание текста через Tesseract с метриками выполнения."""
        start_time = time.perf_counter()

        # Расширенная предобработка для улучшения качества OCR
        processed_image = self.preprocess_image_advanced(image_cv, image_type)

        # Конвертация обратно в PIL для pytesseract
        processed_pil = Image.fromarray(processed_image)

        # Распознавание текста с улучшенными настройками
        custom_config = f'--psm {psm_mode} --oem 3'

        text = pytesseract.image_to_string(
            processed_pil,
            lang=self.lang,
            config=custom_config,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Tesseract OCR duration: {duration_ms:.1f} ms")

        return OCRResult(
            text=text,
            engine='TESSERACT',
            duration_ms=duration_ms,
            char_count=len(text),
            token_count=len(re.findall(r'[A-Za-zА-Яа-яЁё0-9]+', text)),
            image_type=image_type,
            psm_mode=psm_mode,
            image_width=int(image_cv.shape[1]),
            image_height=int(image_cv.shape[0]),
        )

    def extract_text_easyocr(self, image_cv: np.ndarray, image_type: str) -> str:
        """Распознавание текста через EasyOCR."""
        return self.extract_text_easyocr_with_metrics(
            image_cv,
            image_type,
            self.PSM_MODES.get(image_type, 3),
        ).text

    def extract_text_easyocr_with_metrics(
        self,
        image_cv: np.ndarray,
        image_type: str,
        psm_mode: Optional[int] = None,
    ) -> OCRResult:
        """Распознавание текста через EasyOCR с логированием confidence."""
        psm_mode = psm_mode or self.PSM_MODES.get(image_type, 3)
        min_conf_threshold = self._get_easyocr_threshold()
        start_time = time.perf_counter()

        try:
            # EasyOCR работает лучше с легкой предобработкой
            processed_image = self.preprocess_for_easyocr(image_cv)

            # Распознавание через EasyOCR
            # EasyOCR возвращает список кортежей (bbox, text, confidence)
            ocr_result = self.easyocr_reader.readtext(processed_image)

            confidences = [float(result[2]) for result in ocr_result]
            if confidences:
                avg_confidence = float(np.mean(confidences))
                min_confidence = float(np.min(confidences))
                max_confidence = float(np.max(confidences))
                high_conf_count = sum(1 for c in confidences if c >= 0.7)
            else:
                avg_confidence = 0.0
                min_confidence = 0.0
                max_confidence = 0.0
                high_conf_count = 0

            logger.info(
                "EasyOCR статистика: %d блоков, avg_conf=%.2f, "
                "min=%.2f, max=%.2f, >=0.7: %d, порог=%.2f",
                len(ocr_result),
                avg_confidence,
                min_confidence,
                max_confidence,
                high_conf_count,
                min_conf_threshold,
            )

            # Собираем текст только с достаточной уверенностью
            text_parts = [
                result[1] for result in ocr_result
                if float(result[2]) >= min_conf_threshold
            ]
            text = '\n'.join(text_parts)

            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"EasyOCR распознал {len(text)} символов за {duration_ms:.1f} ms (порог: {min_conf_threshold})")

            return OCRResult(
                text=text,
                engine='EASYOCR',
                duration_ms=duration_ms,
                char_count=len(text),
                token_count=len(re.findall(r'[A-Za-zА-Яа-яЁё0-9]+', text)),
                image_type=image_type,
                psm_mode=psm_mode,
                image_width=int(image_cv.shape[1]),
                image_height=int(image_cv.shape[0]),
                confidence=avg_confidence,
                blocks_total=len(ocr_result),
                blocks_above_threshold=sum(1 for c in confidences if c >= min_conf_threshold),
                avg_confidence=avg_confidence,
                min_confidence=min_confidence,
                max_confidence=max_confidence,
                high_conf_count=high_conf_count,
                min_confidence_threshold=min_conf_threshold,
            )

        except Exception as e:
            logger.warning(f"Ошибка EasyOCR: {e}. Переключаемся на Tesseract.")
            fallback = self.extract_text_tesseract_with_metrics(image_cv, image_type, psm_mode)
            fallback.quality_flags.append('easyocr_fallback')
            return fallback

    def preprocess_for_easyocr(self, image_cv: np.ndarray) -> np.ndarray:
        """
        Легкая предобработка специально для EasyOCR.
        EasyOCR имеет свою нейросеть и не нуждается в агрессивной бинаризации.

        Args:
            image_cv: Изображение в формате OpenCV.

        Returns:
            Обработанное изображение.
        """
        try:
            # 1. Конвертация в оттенки серого
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            logger.debug("EasyOCR: Конвертация в grayscale")

            # 2. Уменьшение шума (bilateral filter сохраняет края)
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            logger.debug("EasyOCR: Уменьшение шума")

            # 3. Легкое усиление контраста (CLAHE с мягкими параметрами)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            logger.debug("EasyOCR: Легкое улучшение контраста")

            # 4. Масштабирование 2x (EasyOCR чувствителен к размеру)
            scale_factor = 2.0
            scaled = cv2.resize(
                enhanced,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_LANCZOS4,
            )
            logger.debug(f"EasyOCR: Масштабирование {scale_factor}x")

            return scaled

        except Exception as e:
            logger.warning(f"Ошибка предобработки EasyOCR: {e}. Используется оригинал.")
            return image_cv

    def detect_image_type(self, image_cv: np.ndarray) -> str:
        """Определяет тип изображения для выбора PSM режима."""
        try:
            if image_cv is None or image_cv.size == 0:
                return 'unknown'

            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape[:2]
            total_pixels = max(height * width, 1)
            mean = cv2.mean(gray)[0]
            std = cv2.meanStdDev(gray)[1][0][0]
            non_zero = cv2.countNonZero(gray)
            edges = cv2.Canny(gray, 50, 150)
            edge_ratio = cv2.countNonZero(edges) / total_pixels

            if non_zero < total_pixels * 0.01 or (mean > 250 and std < 5):
                return 'blank'

            if mean < 40:
                return 'dark'

            if edge_ratio > 0.015 and mean > 180:
                return 'document'

            if edge_ratio > 0.005:
                return 'sparse'

            return 'auto'

        except Exception as e:
            logger.warning(f"Не удалось определить тип изображения: {e}")
            return 'auto'

    def preprocess_image_advanced(self, image_cv: np.ndarray, image_type: str = 'auto') -> np.ndarray:
        """
        Продвинутое предобработка изображения с помощью OpenCV.
        Адаптируется под тип изображения.

        Args:
            image_cv: Изображение в формате OpenCV.
            image_type: Тип изображения ('document', 'sparse', 'raw_line', 'auto').

        Returns:
            Обработанное изображение.
        """
        try:
            # 1. Конвертация в оттенки серого
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            logger.debug(f"Шаг 1: Конвертация в grayscale (тип: {image_type})")

            # 2. Уменьшение шума с сохранением краев (bilateral filter)
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            logger.debug("Шаг 2: Уменьшение шума (bilateral filter)")

            # 3. Усиление резкости через sharpening kernel
            kernel_sharpen = np.array([[-1, -1, -1],
                                       [-1, 9, -1],
                                       [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
            logger.debug("Шаг 3: Усиление резкости")

            # 4. Увеличение контраста через CLAHE (ограниченная адаптивная гистограмма)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16, 16))
            enhanced = clahe.apply(sharpened)
            logger.debug("Шаг 4: Улучшение контраста (CLAHE)")

            # 5. Масштабирование изображения для лучшего распознавания
            # Для хорошего качества скриншотов - 3x для максимальной четкости
            scale_factor = 3.0
            scaled = cv2.resize(
                enhanced,
                (int(enhanced.shape[1] * scale_factor), int(enhanced.shape[0] * scale_factor)),
                interpolation=cv2.INTER_LANCZOS4,  # Лучшее качество масштабирования
            )
            logger.debug(f"Шаг 5: Масштабирование {scale_factor}x (LANCZOS4)")

            # 6. Дополнительная обработка для разных типов
            if image_type == 'document':
                # Для документов - бинаризация + дилатация
                _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.dilate(binary, kernel, iterations=2)
                logger.debug("Шаг 6: Бинаризация + дилатация (документ)")

            elif image_type == 'sparse':
                # Для интерфейсов - только бинаризация
                _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed = binary
                logger.debug("Шаг 6: Бинаризация (интерфейс)")

            else:
                # По умолчанию - бинаризация + легкая дилатация
                _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                kernel = np.ones((1, 1), np.uint8)
                processed = cv2.dilate(binary, kernel, iterations=1)
                logger.debug("Шаг 6: Бинаризация + легкая дилатация (авто)")

            logger.debug("Предобработка OpenCV завершена")
            return processed

        except Exception as e:
            logger.warning(f"Ошибка предобработки OpenCV: {e}. Используется оригинал.")
            return image_cv

    def clean_text(self, text: str) -> str:
        """
        Очистка и нормализация распознанного текста.

        Args:
            text: Сырой текст из OCR.

        Returns:
            Очищенный текст.
        """
        # Удаление лишних пробелов и нормализация
        # Удаление множественных пробелов
        text = re.sub(r'\s+', ' ', text)
        # Удаление специальных символов в начале/конце
        text = text.strip()
        return text
