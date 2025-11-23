from decimal import Decimal
import re

def Converter_decimal(texto):

    if not texto:
        return None

    texto_limpo = re.sub(r'[^\d,.]', '', texto)

    if not texto_limpo:
        return None

    if ',' in texto_limpo:
        if texto_limpo.count('.') > 0 and texto_limpo.rfind(',') > texto_limpo.rfind('.'):
            texto_limpo = texto_limpo.replace('.', '')
        texto_limpo = texto_limpo.replace(',', '.')
    texto_limpo = re.sub(r'\.{2,}', '.', texto_limpo)
    texto_limpo = texto_limpo.strip('.')
    try:
        return Decimal(texto_limpo)
    except Exception:
        return None


def Converter_inteiro(texto):

    if not texto:
        return None
    try:
        texto_limpo = ''.join(filter(str.isdigit, texto))
        return int(texto_limpo or 0)
    except ValueError:
        return None
