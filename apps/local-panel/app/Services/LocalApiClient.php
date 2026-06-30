<?php

declare(strict_types=1);

namespace App\Services;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Session;

/**
 * HTTP-клиент к local-api. Панель stateless — все данные через API.
 */
final class LocalApiClient
{
    public function baseUrl(): string
    {
        return rtrim((string) config('autoscale.local_api_url'), '/');
    }

    public function wsUrl(): string
    {
        return rtrim((string) config('autoscale.local_api_ws_url'), '/');
    }

    private function client(): PendingRequest
    {
        $request = Http::baseUrl($this->baseUrl())
            ->acceptJson()
            ->timeout(30);

        if ($token = Session::get('api_token')) {
            $request = $request->withToken($token);
        }

        return $request;
    }

    public function login(string $email, string $password): array
    {
        $response = $this->client()->post('/api/auth/login', [
            'email' => $email,
            'password' => $password,
        ]);

        $response->throw();
        $data = $response->json();

        Session::put('api_token', $data['access_token']);
        Session::put('api_user', $data['user']);

        return $data;
    }

    public function logout(): void
    {
        try {
            $this->client()->post('/api/auth/logout');
        } catch (\Throwable) {
            // игнорируем ошибки при logout
        }
        Session::forget(['api_token', 'api_user']);
    }

    public function get(string $path): array
    {
        return $this->client()->get($path)->throw()->json();
    }

    public function post(string $path, array $data = []): array
    {
        return $this->client()->post($path, $data)->throw()->json();
    }

    public function health(): array
    {
        return Http::baseUrl($this->baseUrl())->get('/api/health')->json();
    }

    public function licenseStatus(): array
    {
        return $this->get('/api/license/status');
    }
}
