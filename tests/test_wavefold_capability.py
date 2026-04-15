import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT / 'DoENGINE' / 'apps'
if str(APPS) not in sys.path:
    sys.path.insert(0, str(APPS))

from dodo_engine3d import DodoPseudo3DEngine  # noqa: E402
from homelair_capability import rsa_pkcs1v15_sha256_sign, verify_capability_payload  # noqa: E402


TEST_TRUSTED_KEYS = {
    'test-key-2026': {
        'algorithm': 'rsa-pkcs1v15-sha256',
        'modulus_b64': 'xPau+paOvlc1d6IuQrqrfmv5h/WMKiGZ722dKdktSpIyvkAXQ/Xe3ClaSmfa79osvw6ge48Ln442HliDcwxQWqRHGw9YCxKm8tYvlx7WKcX1f/ylEZv3uxzc3W926SZWMp3OfvPhn/JF2L/zNcExh+p2z1oC1SU1fI1uj4qpdm0=',
        'exponent_b64': 'AQAB',
    }
}

TEST_PRIVATE_EXPONENT_B64 = 'u0PnHa2jzejQlwwFe8BLaQlz2AZn227TEsdfE/i+jRXvVN9Ov3i3CQ/wHqobiMwgmw5nGtLoNC1b2wJBCFN+2OPwvTTbS+zwWZiYAk+5fKam32wightEMnjr25gaVAOleErzc56aJIBwOJmLksdM4C36gSpIp99AolgeisJoGuk='


def _signed_payload() -> dict:
    payload = {
        'capability_id': 'test-wavefold',
        'issued_to': 'unit-test',
        'key_id': 'test-key-2026',
        'features': ['wavefold.pro'],
        'limits': {
            'max_fold_amplitude': 1.0,
            'fallback_fold_amplitude': 0.08,
            'fallback_inward_bias': 0.05,
        },
        'expires_utc': '2030-01-01T00:00:00Z',
    }
    message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    payload['signature_b64'] = rsa_pkcs1v15_sha256_sign(
        message,
        modulus_b64=TEST_TRUSTED_KEYS['test-key-2026']['modulus_b64'],
        private_exponent_b64=TEST_PRIVATE_EXPONENT_B64,
    )
    return payload


def test_verify_capability_payload_accepts_valid_signature():
    result = verify_capability_payload(_signed_payload(), trusted_keys=TEST_TRUSTED_KEYS)

    assert result['valid'] is True
    assert result['mode'] == 'premium'
    assert 'wavefold.pro' in result['features']


def test_playhub_wavefold_scene_renders_with_limited_capability_by_default():
    scene_path = ROOT / 'HOMElair' / 'assets' / 'scenes' / 'playhub_sanctuary_plaza.scene.json'
    engine = DodoPseudo3DEngine(width=320, height=180, scene_manifest_path=scene_path)

    _image, stats = engine.render_preview(orbit=0.5, elevation=0.2, shader_mix=0.85, time_s=1.0)

    assert stats['wavefold_meshes'] >= 1
    assert stats['capability_mode'] == 'limited'


def test_wavefold_scene_renders_with_premium_capability_when_signed_bundle_is_present(tmp_path, monkeypatch):
    capability_path = tmp_path / 'homelair_capability.json'
    capability_path.write_text(json.dumps(_signed_payload(), indent=2), encoding='utf-8')
    monkeypatch.setenv('HOMELAIR_CAPABILITY_PATH', str(capability_path))

    scene_path = ROOT / 'HOMElair' / 'assets' / 'scenes' / 'playhub_sanctuary_plaza.scene.json'
    engine = DodoPseudo3DEngine(width=320, height=180)
    engine.capability_bundle = verify_capability_payload(_signed_payload(), trusted_keys=TEST_TRUSTED_KEYS)
    engine.load_scene_manifest(scene_path)

    _image, stats = engine.render_preview(orbit=0.5, elevation=0.2, shader_mix=0.85, time_s=1.0)

    assert stats['wavefold_meshes'] >= 1
    assert stats['capability_mode'] == 'premium'