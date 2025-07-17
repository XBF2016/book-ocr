import traceback, sys, logging
from pathlib import Path
from boocr.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

pdf_path = Path('input')
# pick first pdf
pdf_files = list(pdf_path.glob('*.pdf'))
if not pdf_files:
    print('No pdf in input')
    sys.exit(1)
input_pdf = pdf_files[0]
output_pdf = Path('debug_out.pdf')

try:
    run_pipeline(str(input_pdf), str(output_pdf), params={
        'save_intermediate': False,
        'det_model_dir': 'boocr/ocr_model/PP-OCRv5_server_det_infer',
        'rec_model_dir': 'boocr/ocr_model/chinese_cht_PP-OCRv3_mobile_rec_infer',
        'auto_download': False,
    })
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
print('Pipeline finished')
