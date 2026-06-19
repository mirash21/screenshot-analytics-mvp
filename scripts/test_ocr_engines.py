"""
Скрипт для A/B тестирования OCR движков (Tesseract vs EasyOCR).

Запускает оба движка на одном наборе скриншотов, сравнивает:
- время обработки;
- длину распознанного текста;
- OCR confidence;
- количество EasyOCR-блоков выше confidence threshold;
- итоговый quality score.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OCR_ANALYZER_DIR = PROJECT_ROOT / 'ocr-analyzer'
if OCR_ANALYZER_DIR.exists():
    sys.path.insert(0, str(OCR_ANALYZER_DIR))
else:
    sys.path.insert(0, '/app')

STORAGE_DIR = Path('/app/storage') if Path('/app/storage').exists() else PROJECT_ROOT / 'storage'
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

from ocr_engine import OCREngine

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(STORAGE_DIR / 'ocr_comparison.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def create_tesseract_engine() -> OCREngine:
    """Создает OCR-движок, принудительно использующий Tesseract."""
    old_value = os.environ.get('OCR_ENGINE')
    os.environ['OCR_ENGINE'] = 'TESSERACT'
    try:
        engine = OCREngine(lang='rus+eng')
    finally:
        if old_value is None:
            os.environ.pop('OCR_ENGINE', None)
        else:
            os.environ['OCR_ENGINE'] = old_value

    engine.cache_enabled = False
    return engine


def create_easyocr_engine() -> OCREngine:
    """Создает OCR-движок, принудительно использующий EasyOCR."""
    old_value = os.environ.get('OCR_ENGINE')
    os.environ['OCR_ENGINE'] = 'EASYOCR'
    try:
        engine = OCREngine(lang='rus+eng')
    finally:
        if old_value is None:
            os.environ.pop('OCR_ENGINE', None)
        else:
            os.environ['OCR_ENGINE'] = old_value

    engine.cache_enabled = False
    return engine


def run_engine(engine: OCREngine, image_path: str, engine_name: str) -> Dict[str, Any]:
    """Запускает один OCR-движок на изображении и возвращает метрики."""
    total_start = time.perf_counter()
    try:
        result = engine.extract_text_with_metrics(image_path)
        metrics = result.metrics_dict()
        metrics['total_time_ms'] = (time.perf_counter() - total_start) * 1000
        metrics['error'] = None
        return metrics
    except Exception as e:
        logger.error(f"Ошибка OCR-движка {engine_name} для {image_path}: {e}", exc_info=True)
        return {
            'engine': engine_name,
            'text': '',
            'error': str(e),
            'total_time_ms': (time.perf_counter() - total_start) * 1000,
            'char_count': 0,
            'token_count': 0,
            'confidence': 0.0,
        }


def compare_ocr_engines(
    image_path: str,
    tesseract_engine: OCREngine,
    easyocr_engine: OCREngine,
) -> Dict[str, Any]:
    """
    Сравнивает Tesseract и EasyOCR на одном изображении.

    Args:
        image_path: Путь к изображению.
        tesseract_engine: OCR-движок Tesseract.
        easyocr_engine: OCR-движок EasyOCR.

    Returns:
        Словарь с результатами сравнения.
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Тестирование: {image_path}")
    logger.info(f"{'=' * 60}")

    results: Dict[str, Any] = {
        'image': image_path,
        'tesseract': run_engine(tesseract_engine, image_path, 'TESSERACT'),
        'easyocr': run_engine(easyocr_engine, image_path, 'EASYOCR'),
    }

    log_engine_result('TESSERACT', results['tesseract'])
    log_engine_result('EASYOCR', results['easyocr'])

    results['recommendation'] = recommend_engine(results['tesseract'], results['easyocr'])
    logger.info(
        "Рекомендация для изображения: %s",
        results['recommendation']['engine'],
    )

    return results


def log_engine_result(engine_name: str, metrics: Dict[str, Any]) -> None:
    """Логирует результат одного OCR-движка."""
    error = metrics.get('error')
    if error:
        logger.error("%s ошибка: %s", engine_name, error)
        return

    logger.info("%s:", engine_name)
    logger.info("  Время: %.2f сек", metrics.get('total_time_ms', 0.0) / 1000)
    logger.info("  Длина текста: %d символов", metrics.get('char_count', 0))
    logger.info("  Токены: %d", metrics.get('token_count', 0))
    logger.info("  Confidence: %.2f", metrics.get('confidence', 0.0))
    logger.info("  Image type: %s, PSM: %s", metrics.get('image_type'), metrics.get('psm_mode'))
    logger.info("  Quality flags: %s", ','.join(metrics.get('quality_flags', [])) or 'none')

    if metrics.get('engine') == 'EASYOCR':
        logger.info(
            "  EasyOCR blocks: %d/%d выше порога %.2f, avg_conf=%.2f, min=%.2f, max=%.2f",
            metrics.get('blocks_above_threshold', 0),
            metrics.get('blocks_total', 0),
            metrics.get('min_confidence_threshold', 0.0) or 0.0,
            metrics.get('avg_confidence', 0.0) or 0.0,
            metrics.get('min_confidence', 0.0) or 0.0,
            metrics.get('max_confidence', 0.0) or 0.0,
        )

    text = metrics.get('text', '')
    logger.info("  Текст (первые 200 символов): %s", text[:200].replace('\n', ' '))


def safe_average(values: List[float]) -> float:
    """Безопасно считает среднее значение."""
    return sum(values) / len(values) if values else 0.0


def engine_score(metrics: Dict[str, Any]) -> float:
    """Считает quality score: качество текста с учетом confidence и скорости."""
    if metrics.get('error'):
        return 0.0

    char_count = float(metrics.get('char_count', 0))
    confidence = float(metrics.get('confidence', 0.0))
    total_time_ms = max(float(metrics.get('total_time_ms', 0.0)), 1.0)

    quality = char_count * (0.6 + confidence * 0.4)
    return quality / total_time_ms


def recommend_engine(tesseract: Dict[str, Any], easyocr: Dict[str, Any]) -> Dict[str, Any]:
    """Рекомендует движок по итогам одного изображения."""
    tesseract_score = engine_score(tesseract)
    easyocr_score = engine_score(easyocr)

    if easyocr_score > tesseract_score * 1.1:
        engine = 'EASYOCR'
        reason = 'лучший quality score'
    elif tesseract_score > easyocr_score * 1.1:
        engine = 'TESSERACT'
        reason = 'лучший quality score'
    else:
        tesseract_time = float(tesseract.get('total_time_ms', 0.0))
        easyocr_time = float(easyocr.get('total_time_ms', 0.0))
        engine = 'TESSERACT' if tesseract_time <= easyocr_time else 'EASYOCR'
        reason = 'похожее качество, выбран более быстрый движок'

    return {
        'engine': engine,
        'reason': reason,
        'tesseract_score': round(tesseract_score, 6),
        'easyocr_score': round(easyocr_score, 6),
    }


def find_images(screenshots_dir: str, limit: int) -> List[str]:
    """Ищет изображения для A/B-теста."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
    images: List[str] = []

    for path in sorted(Path(screenshots_dir).rglob('*')):
        if path.is_file() and path.suffix.lower() in image_extensions:
            images.append(str(path))
            if len(images) >= limit:
                break

    return images


def summarize_results(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Собирает итоговую статистику по всем изображениям."""
    summary: Dict[str, Any] = {
        'images': len(all_results),
        'tesseract': {},
        'easyocr': {},
        'recommendations': {
            'TESSERACT': 0,
            'EASYOCR': 0,
        },
    }

    for engine_key in ['tesseract', 'easyocr']:
        engine_results = [result[engine_key] for result in all_results]
        success_results = [result for result in engine_results if not result.get('error')]

        summary[engine_key] = {
            'success_rate': len(success_results) / len(engine_results) if engine_results else 0.0,
            'avg_time_ms': safe_average([result.get('total_time_ms', 0.0) for result in success_results]),
            'avg_chars': safe_average([result.get('char_count', 0) for result in success_results]),
            'avg_tokens': safe_average([result.get('token_count', 0) for result in success_results]),
            'avg_confidence': safe_average([result.get('confidence', 0.0) for result in success_results]),
            'avg_score': safe_average([
                engine_score(result) for result in success_results
            ]),
            'errors': sum(1 for result in engine_results if result.get('error')),
        }

    for result in all_results:
        recommendation = result.get('recommendation', {}).get('engine')
        if recommendation in summary['recommendations']:
            summary['recommendations'][recommendation] += 1

    if summary['easyocr']['avg_score'] > summary['tesseract']['avg_score'] * 1.1:
        overall = 'EASYOCR'
        reason = 'лучший средний quality score'
    elif summary['tesseract']['avg_score'] > summary['easyocr']['avg_score'] * 1.1:
        overall = 'TESSERACT'
        reason = 'лучший средний quality score'
    else:
        overall = 'TESSERACT' if summary['tesseract']['avg_time_ms'] <= summary['easyocr']['avg_time_ms'] else 'EASYOCR'
        reason = 'похожее качество, выбран более быстрый движок'

    summary['overall_recommendation'] = {
        'engine': overall,
        'reason': reason,
    }

    return summary


def log_summary(summary: Dict[str, Any]) -> None:
    """Выводит итоговую статистику в лог."""
    logger.info("\n" + "=" * 60)
    logger.info("ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 60)

    for engine_key, label in [('tesseract', 'Tesseract'), ('easyocr', 'EasyOCR')]:
        metrics = summary[engine_key]
        logger.info("%s:", label)
        logger.info("  Success rate: %.1f%%", metrics['success_rate'] * 100)
        logger.info("  Avg time: %.2f сек", metrics['avg_time_ms'] / 1000)
        logger.info("  Avg chars: %.1f", metrics['avg_chars'])
        logger.info("  Avg confidence: %.2f", metrics['avg_confidence'])
        logger.info("  Avg score: %.3f", metrics['avg_score'])
        logger.info("  Errors: %d", metrics['errors'])

    recommendations = summary['recommendations']
    logger.info(
        "Per-image recommendations: Tesseract=%d, EasyOCR=%d",
        recommendations['TESSERACT'],
        recommendations['EASYOCR'],
    )

    overall = summary['overall_recommendation']
    logger.info(
        "\n🏆 РЕКОМЕНДАЦИЯ: Использовать %s (%s)",
        overall['engine'],
        overall['reason'],
    )


def run_comparison(screenshots_dir: str, limit: int = 10, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Запускает сравнение на наборе скриншотов.

    Args:
        screenshots_dir: Директория со скриншотами.
        limit: Количество скриншотов для теста.
        output_path: Путь для JSON-отчета.
    """
    logger.info("=" * 60)
    logger.info("A/B ТЕСТИРОВАНИЕ OCR ДВИЖКОВ")
    logger.info(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)

    images = find_images(screenshots_dir, limit)
    if not images:
        logger.error(f"Изображения не найдены в {screenshots_dir}")
        return {'images': 0, 'error': f'No images found in {screenshots_dir}'}

    logger.info(f"Найдено {len(images)} изображений для тестирования\n")

    logger.info("Инициализация OCR-движков...")
    tesseract_engine = create_tesseract_engine()
    easyocr_engine = create_easyocr_engine()

    all_results: List[Dict[str, Any]] = []
    for i, image_path in enumerate(images, 1):
        logger.info(f"\n[{i}/{len(images)}]")
        all_results.append(compare_ocr_engines(image_path, tesseract_engine, easyocr_engine))

    summary = summarize_results(all_results)
    payload = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'screenshots_dir': screenshots_dir,
        'limit': limit,
        'results': all_results,
        'summary': summary,
    }

    output_path = output_path or os.getenv('OCR_COMPARISON_OUTPUT', '/app/storage/ocr_comparison.json')
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    log_summary(summary)
    logger.info("\nJSON-отчет сохранен в: %s", output_path)
    logger.info("Лог сохранен в: /app/storage/ocr_comparison.log")

    return payload


if __name__ == "__main__":
    screenshots_dir = os.getenv('SCREENSHOTS_DIR', '/app/storage/screenshots')
    limit = int(os.getenv('TEST_LIMIT', '10'))
    output_path = os.getenv('OCR_COMPARISON_OUTPUT')

    run_comparison(screenshots_dir, limit, output_path)
