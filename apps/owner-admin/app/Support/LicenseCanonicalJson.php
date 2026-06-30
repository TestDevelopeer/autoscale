<?php

declare(strict_types=1);

namespace App\Support;

/**
 * Каноническая JSON-сериализация для подписи лицензии (совместима с Python license-core).
 */
final class LicenseCanonicalJson
{
    public static function encode(array $payload): string
    {
        self::ksortRecursive($payload);

        return json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    }

    private static function ksortRecursive(array &$array): void
    {
        ksort($array);
        foreach ($array as &$value) {
            if (is_array($value)) {
                self::ksortRecursive($value);
            }
        }
    }
}
