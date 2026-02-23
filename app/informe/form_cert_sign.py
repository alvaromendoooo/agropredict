from pyhanko.sign import signers
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.sign.signers import PdfSigner
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

import os

load_dotenv()

def main():

    hoy = date.today()
    
    BASE_DIR = Path(__file__).resolve().parent
    INFORME_DIR = BASE_DIR

    nombre_archivo = f"reporte_riesgos_heladas_{hoy}.pdf"

    ruta_pdf = INFORME_DIR / nombre_archivo

    password = os.getenv("PASSWORD_CERTIFICADO")

    if not password:
        raise ValueError("No se ha encuentrado la variable PASSWORD_CERTIFICADO")
    
    with open(ruta_pdf, "rb") as f:
        w = IncrementalPdfFileWriter(f)

        signer = signers.SimpleSigner.load(
            key_file = INFORME_DIR / "clave.key",
            cert_file = INFORME_DIR / "certificado.crt",
            key_passphrase = password.encode("utf-8")
        )

        pdf_signer = PdfSigner(
            signature_meta = signers.PdfSignatureMetadata(field_name = "Firma Reporte EPCC"),
            signer = signer,
            new_field_spec=SigFieldSpec(
                sig_field_name="Firma Reporte EPCC",
                box=(50, 50, 250, 150)
            )
        )

        with open(INFORME_DIR / f"reporte_firmado_{hoy}.pdf", "wb") as outf:
            pdf_signer.sign_pdf(w, output = outf)

if __name__ == "__main__":
    main()