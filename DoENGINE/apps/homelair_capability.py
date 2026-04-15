from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


SHA256_DIGESTINFO_PREFIX = bytes.fromhex('3031300d060960864801650304020105000420')

TRUSTED_PUBLIC_KEYS = {
    'homelair-main-2026': {
        'algorithm': 'rsa-pkcs1v15-sha256',
        'modulus_b64': '43piIbgtv5D0q4jkfVgxo2dRkJQkzFA68THUl1HPNw7SBUt16Nt4Ofvq6UKKAMbbY+MDo031oAn6D9UOcUClVAD2YApRIxt56vZUv2w1SC3QfXpoc7gC3ohtmwS2iZKRWrX8gYEltp3nhNRoIZ1+FPs4dy2tmuMOrr76doBkf/SRgNTqhUXjXLG8U0/XvDR1sdn7TwAqa/pasye9KxEt5Db3az0VrD0i8Y0Z+kBeEM5WgxkIjjcQ/KRciY3OjC+zw28H1SOjWrESJlgb7Vw+lL1cgFgk1wLbKIc49C86v3EFbQSMZmlqaYEVjSL2Rgi+6h/qvtzRvGg89mEh3zXkZQ==',
        'exponent_b64': 'AQAB',
    }
}


def load_trusted_keys_bundle(path: Path | None = None) -> dict:
    raw_path = path or os.environ.get('HOMELAIR_TRUSTED_KEYS_PATH')
    if raw_path is None:
        return dict(TRUSTED_PUBLIC_KEYS)
    keys_path = Path(str(raw_path))
    if not keys_path.exists():
        return dict(TRUSTED_PUBLIC_KEYS)
    payload = json.loads(keys_path.read_text(encoding='utf-8-sig'))
    if not isinstance(payload, dict):
        return dict(TRUSTED_PUBLIC_KEYS)
    merged = dict(TRUSTED_PUBLIC_KEYS)
    for key_id, record in payload.items():
        if isinstance(record, dict):
            merged[str(key_id)] = record
    return merged


def _b64_to_int(value: str) -> int:
    return int.from_bytes(base64.b64decode(value), 'big')


def _normalize_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = str(value).replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonicalize_capability_payload(payload: dict) -> bytes:
    clean_payload = {key: value for key, value in payload.items() if key != 'signature_b64'}
    return json.dumps(clean_payload, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _build_pkcs1_v15_block(message: bytes, modulus_bytes: int) -> bytes:
    digest = hashlib.sha256(message).digest()
    digest_info = SHA256_DIGESTINFO_PREFIX + digest
    padding_length = modulus_bytes - len(digest_info) - 3
    if padding_length < 8:
        raise ValueError('RSA modulus is too small for PKCS#1 v1.5 SHA-256 signing.')
    return b'\x00\x01' + (b'\xff' * padding_length) + b'\x00' + digest_info


def rsa_pkcs1v15_sha256_verify(message: bytes, signature_b64: str, *, modulus_b64: str, exponent_b64: str) -> bool:
    modulus = _b64_to_int(modulus_b64)
    exponent = _b64_to_int(exponent_b64)
    signature = base64.b64decode(signature_b64)
    modulus_bytes = (modulus.bit_length() + 7) // 8
    if len(signature) != modulus_bytes:
        return False
    decrypted = pow(int.from_bytes(signature, 'big'), exponent, modulus).to_bytes(modulus_bytes, 'big')
    return decrypted == _build_pkcs1_v15_block(message, modulus_bytes)


def rsa_pkcs1v15_sha256_sign(message: bytes, *, modulus_b64: str, private_exponent_b64: str) -> str:
    modulus = _b64_to_int(modulus_b64)
    private_exponent = _b64_to_int(private_exponent_b64)
    modulus_bytes = (modulus.bit_length() + 7) // 8
    encoded = _build_pkcs1_v15_block(message, modulus_bytes)
    signature_int = pow(int.from_bytes(encoded, 'big'), private_exponent, modulus)
    return base64.b64encode(signature_int.to_bytes(modulus_bytes, 'big')).decode('ascii')


def verify_capability_payload(payload: dict, *, trusted_keys: dict | None = None, now_utc: datetime | None = None) -> dict:
    trusted = trusted_keys or TRUSTED_PUBLIC_KEYS
    key_id = str(payload.get('key_id', ''))
    signature_b64 = payload.get('signature_b64')
    if not key_id:
        return {'valid': False, 'reason': 'missing-key-id', 'features': [], 'limits': {}, 'mode': 'limited'}
    if key_id not in trusted:
        return {'valid': False, 'reason': 'untrusted-key-id', 'features': [], 'limits': {}, 'mode': 'limited', 'key_id': key_id}
    if not isinstance(signature_b64, str) or not signature_b64:
        return {'valid': False, 'reason': 'missing-signature', 'features': [], 'limits': {}, 'mode': 'limited', 'key_id': key_id}
    message = canonicalize_capability_payload(payload)
    key_record = trusted[key_id]
    verified = rsa_pkcs1v15_sha256_verify(
        message,
        signature_b64,
        modulus_b64=str(key_record['modulus_b64']),
        exponent_b64=str(key_record['exponent_b64']),
    )
    if not verified:
        return {'valid': False, 'reason': 'signature-mismatch', 'features': [], 'limits': {}, 'mode': 'limited', 'key_id': key_id}
    expires_at = _normalize_timestamp(payload.get('expires_utc'))
    current_time = now_utc or datetime.now(timezone.utc)
    if expires_at is not None and current_time > expires_at:
        return {'valid': False, 'reason': 'expired', 'features': [], 'limits': {}, 'mode': 'limited', 'key_id': key_id, 'expires_utc': payload.get('expires_utc')}
    features = [str(feature) for feature in payload.get('features', []) if isinstance(feature, str)]
    limits = payload.get('limits', {}) if isinstance(payload.get('limits', {}), dict) else {}
    return {
        'valid': True,
        'reason': 'verified',
        'mode': 'premium',
        'key_id': key_id,
        'capability_id': payload.get('capability_id'),
        'issued_to': payload.get('issued_to'),
        'expires_utc': payload.get('expires_utc'),
        'features': features,
        'limits': limits,
    }


def load_capability_bundle(path: Path | None = None, *, trusted_keys: dict | None = None) -> dict:
    raw_path = path or os.environ.get('HOMELAIR_CAPABILITY_PATH')
    effective_trusted_keys = trusted_keys or load_trusted_keys_bundle()
    if raw_path is None:
        return {'loaded': False, 'valid': False, 'reason': 'no-capability-path', 'mode': 'limited', 'features': [], 'limits': {}}
    capability_path = Path(str(raw_path))
    if not capability_path.exists():
        return {'loaded': False, 'valid': False, 'reason': 'capability-file-missing', 'mode': 'limited', 'path': str(capability_path), 'features': [], 'limits': {}}
    payload = json.loads(capability_path.read_text(encoding='utf-8-sig'))
    if not isinstance(payload, dict):
        return {'loaded': False, 'valid': False, 'reason': 'invalid-capability-payload', 'mode': 'limited', 'path': str(capability_path), 'features': [], 'limits': {}}
    result = verify_capability_payload(payload, trusted_keys=effective_trusted_keys)
    result['loaded'] = True
    result['path'] = str(capability_path)
    return result


def capability_has_feature(bundle: dict | None, feature: str) -> bool:
    if not isinstance(bundle, dict) or not bundle.get('valid'):
        return False
    return feature in bundle.get('features', [])
