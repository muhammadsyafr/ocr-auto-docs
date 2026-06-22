"""Rule-based document classifier (PRD FR-005).

Keyword/regex scoring -> ktp | academic_certificate | employment_certificate.
Returns (doc_type, confidence). LLM fallback handled by caller when low.
"""
import re

KTP_KEYWORDS = ["nik", "provinsi", "kabupaten", "kota", "tempat/tgl lahir",
                "kewarganegaraan", "golongan darah", "kartu tanda penduduk"]
ACADEMIC_KEYWORDS = ["ijazah", "sttb", "sekolah", "universitas", "diploma",
                     "sarjana", "telah lulus", "nomor seri", "diberikan kepada",
                     "tanda tamat belajar"]
EMPLOYMENT_KEYWORDS = ["surat keterangan kerja", "perusahaan", "company",
                       "menerangkan bahwa", "jabatan", "bekerja", "pt ", "ltd",
                       "employment"]

NIK_RE = re.compile(r"\b\d{16}\b")


def classify(text: str) -> tuple[str, float]:
    low = text.lower()

    scores = {
        "ktp": sum(1 for k in KTP_KEYWORDS if k in low),
        "academic_certificate": sum(1 for k in ACADEMIC_KEYWORDS if k in low),
        "employment_certificate": sum(1 for k in EMPLOYMENT_KEYWORDS if k in low),
    }
    # NIK present is strong KTP signal
    if NIK_RE.search(text):
        scores["ktp"] += 2

    best = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confidence = scores[best] / total
    if scores[best] == 0:
        return "academic_certificate", 0.0  # unknown -> let LLM/caller decide
    return best, round(confidence, 2)
