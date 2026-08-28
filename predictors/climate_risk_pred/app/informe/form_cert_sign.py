from pyhanko.sign import signers
from pyhanko.sign import fields
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.sign.signers import PdfSigner
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

import os

load_dotenv()

class FirmaService():
    def generar_firma(
        tipo_prediccion : str,
        datos_estimados : Optional[dict] = None,
        ruta_pdf : Optional[str] = None,
    ):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        BASE_DIR = Path(__file__).resolve().parent
        INFORME_DIR = BASE_DIR
        CREDENCIALES_DIR = BASE_DIR / 'assets'

        ruta_pdf = Path(ruta_pdf)
        if not ruta_pdf.exists():
            raise FileNotFoundError(f"No se encontró el pdf en : {ruta_pdf}")

        password = os.getenv("PASSWORD_CERTIFICADO")

        if not password:
            raise ValueError("No se ha encuentrado la variable PASSWORD_CERTIFICADO")
        
        with open(ruta_pdf, "rb") as f:
            w = IncrementalPdfFileWriter(f)
            
            # Calculamos el índice (0 es la primera página)
            num_paginas = w.root['/Pages']['/Count']
            index_last_page = num_paginas - 1

            signer = signers.SimpleSigner.load(
                key_file = CREDENCIALES_DIR / "clave.key",
                cert_file = CREDENCIALES_DIR / "certificado.crt",
                key_passphrase = password.encode("utf-8")
            )

            pdf_signer = PdfSigner(
                signature_meta = signers.PdfSignatureMetadata(field_name = "Firma Reporte EPCC"),
                signer = signer,
                new_field_spec=SigFieldSpec(
                    sig_field_name="Firma Reporte EPCC",
                    on_page = index_last_page,
                    box=(50, 50, 250, 150)
                )
            )

            if tipo_prediccion == "heladas":
                ruta = INFORME_DIR / 'reports' / 'heladas' / f"reporte_heladas_firmado_{timestamp}.pdf"
                with open(ruta, "wb") as outf:
                    pdf_signer.sign_pdf(w, output=outf)
            elif tipo_prediccion == "plagas":
                if datos_estimados:
                    ruta = INFORME_DIR / 'reports' / 'plagas' / f"reporte_plagas_{datos_estimados['cultivo']}_firmado_{timestamp}.pdf"
                    with open(ruta, "wb") as outf:
                        pdf_signer.sign_pdf(w, output=outf)
                else:
                    ruta = INFORME_DIR / 'reports' / 'plagas' / f"reporte_plagas_calculadas_firmado_{timestamp}.pdf"
                    with open(ruta, "wb") as outf:
                        pdf_signer.sign_pdf(w, output=outf)

        return str(os.path.abspath(ruta))