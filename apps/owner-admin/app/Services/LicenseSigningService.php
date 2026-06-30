<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\License;
use App\Support\LicenseCanonicalJson;
use Illuminate\Support\Str;
use RuntimeException;

/**
 * Подпись license file (Ed25519). Private key только на owner-admin.
 */
final class LicenseSigningService
{
    public function sign(License $license, string $machineFingerprint): array
    {
        $privateKeyB64 = config('licensing.signing_private_key');
        if (! $privateKeyB64) {
            throw new RuntimeException('LICENSE_SIGNING_PRIVATE_KEY не настроен');
        }

        $payload = [
            'client_id' => $license->organization_id,
            'expires_at' => $license->expires_at->toIso8601String(),
            'format_version' => 1,
            'grace_days' => $license->grace_days,
            'issued_at' => now()->toIso8601String(),
            'license_id' => $license->id,
            'limits' => $license->limits,
            'machine_fingerprint' => $machineFingerprint,
            'modules' => $license->modules,
            'offline_until' => $license->offline_until?->toIso8601String(),
            'organization_name' => $license->organization?->name ?? '',
            'status' => $license->status,
        ];

        $canonical = LicenseCanonicalJson::encode($payload);
        $seed = base64_decode($privateKeyB64, true);
        if ($seed === false || strlen($seed) !== SODIUM_CRYPTO_SIGN_SEEDBYTES) {
            throw new RuntimeException('Некорректный LICENSE_SIGNING_PRIVATE_KEY');
        }

        $keypair = sodium_crypto_sign_seed_keypair($seed);
        $secretKey = sodium_crypto_sign_secretkey($keypair);
        $signature = sodium_crypto_sign_detached($canonical, $secretKey);

        return [
            'payload' => $payload,
            'signature' => base64_encode($signature),
        ];
    }

    public static function generateActivationCode(): string
    {
        return strtoupper(Str::random(4).'-'.Str::random(4));
    }
}
