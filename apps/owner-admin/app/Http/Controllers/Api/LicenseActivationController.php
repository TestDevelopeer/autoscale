<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\License;
use App\Models\LicenseActivation;
use App\Services\LicenseSigningService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

final class LicenseActivationController extends Controller
{
    public function __construct(private readonly LicenseSigningService $signing) {}

    public function activate(Request $request): JsonResponse
    {
        $data = $request->validate([
            'license_id' => ['required', 'uuid'],
            'activation_code' => ['required', 'string'],
            'machine_fingerprint' => ['required', 'string'],
        ]);

        $license = License::query()
            ->where('id', $data['license_id'])
            ->where('activation_code', $data['activation_code'])
            ->firstOrFail();

        if (in_array($license->status, ['revoked', 'suspended'], true)) {
            return response()->json(['message' => 'Лицензия недоступна'], 403);
        }

        $license->machine_fingerprint = $data['machine_fingerprint'];
        $license->save();

        LicenseActivation::query()->create([
            'license_id' => $license->id,
            'machine_fingerprint' => $data['machine_fingerprint'],
            'hostname' => $request->input('hostname'),
            'product_version' => $request->input('product_version'),
            'activated_at' => now(),
        ]);

        return response()->json($this->signing->sign($license, $data['machine_fingerprint']));
    }

    public function offlineIssue(Request $request): JsonResponse
    {
        $data = $request->validate([
            'license_id' => ['required', 'uuid'],
            'machine_fingerprint' => ['required', 'string'],
        ]);

        $license = License::query()->findOrFail($data['license_id']);

        return response()->json($this->signing->sign($license, $data['machine_fingerprint']));
    }

    public function revoke(License $license): JsonResponse
    {
        $license->update(['status' => 'revoked', 'status_changed_at' => now()]);

        return response()->json(['status' => 'revoked']);
    }

    public function suspend(License $license): JsonResponse
    {
        $license->update(['status' => 'suspended', 'status_changed_at' => now()]);

        return response()->json(['status' => 'suspended']);
    }

    public function renew(Request $request, License $license): JsonResponse
    {
        $data = $request->validate(['expires_at' => ['required', 'date']]);
        $license->update([
            'expires_at' => $data['expires_at'],
            'status' => 'active',
            'status_changed_at' => now(),
        ]);

        return response()->json($license);
    }
}
