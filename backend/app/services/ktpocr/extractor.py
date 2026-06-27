import re
from dataclasses import dataclass, field

from PIL import Image as PILImage

import cv2
import numpy as np
import pytesseract


@dataclass
class KTPInformation:
    nik: str = ""
    nama: str = ""
    tempat_lahir: str = ""
    tanggal_lahir: str = ""
    jenis_kelamin: str = ""
    golongan_darah: str = ""
    alamat: str = ""
    rt: str = ""
    rw: str = ""
    kelurahan_atau_desa: str = ""
    kecamatan: str = ""
    agama: str = ""
    status_perkawinan: str = ""
    pekerjaan: str = ""
    kewarganegaraan: str = ""
    berlaku_hingga: str = "SEUMUR HIDUP"


class KTPOCR:
    def __init__(self, img: np.ndarray):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
        self.result = KTPInformation()
        self._extract(threshed)

    def _ocr(self, img: np.ndarray) -> str:
        return pytesseract.image_to_string(img, lang="ind")

    def _word_to_number(self, word: str) -> str:
        m = {"|": "1"}
        return "".join(m.get(c, c) for c in word)

    def _nik_normalize(self, word: str) -> str:
        m = {"b": "6", "e": "2"}
        return "".join(m.get(c, c) for c in word)

    def _extract(self, threshed: np.ndarray):
        raw = self._ocr(threshed)
        for line in raw.split("\n"):
            if "NIK" in line:
                parts = line.split(":")
                self.result.nik = self._nik_normalize(parts[-1].replace(" ", ""))
            elif "Nama" in line:
                parts = line.split(":")
                self.result.nama = parts[-1].replace("Nama ", "")
            elif "Tempat" in line:
                parts = line.split(":")
                dm = re.search(r"(\d{2}[-/]\d{2}[-/]\d{4})", parts[-1])
                if dm:
                    self.result.tanggal_lahir = dm.group(0)
                    self.result.tempat_lahir = parts[-1].replace(dm.group(0), "")
            elif "Darah" in line:
                gm = re.search(r"(LAKI-LAKI|LAKI|LELAKI|PEREMPUAN)", line)
                if gm:
                    self.result.jenis_kelamin = gm.group(0)
                parts = line.split(":")
                bm = re.search(r"(O|A|B|AB)", parts[-1]) if len(parts) > 1 else None
                self.result.golongan_darah = bm.group(0) if bm else "-"
            elif "Alamat" in line:
                self.result.alamat = self._word_to_number(line).replace("Alamat ", "")
            elif "NO." in line:
                self.result.alamat += " " + line
            elif "Kecamatan" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    self.result.kecamatan = parts[1].strip()
            elif "Desa" in line:
                wrds = [w for w in line.split() if "desa" not in w.lower()]
                self.result.kelurahan_atau_desa = " ".join(wrds)
            elif "Kewarganegaraan" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    self.result.kewarganegaraan = parts[1].strip()
            elif "Pekerjaan" in line:
                wrds = [w for w in line.split() if "-" not in w]
                self.result.pekerjaan = " ".join(wrds).replace("Pekerjaan", "").strip()
            elif "Agama" in line:
                self.result.agama = line.replace("Agama", "").strip()
            elif "Perkawinan" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    self.result.status_perkawinan = parts[1].strip()
            elif "RTRW" in line or "RT" in line:
                line = line.replace("RTRW", "").replace("RT/RW", "")
                parts = line.split("/")
                if len(parts) >= 2:
                    self.result.rt = parts[0].strip()
                    self.result.rw = parts[1].strip()
