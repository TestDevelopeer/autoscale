<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\User;
use App\Services\LocalApiClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\View\View;

final class ApiAuthController extends Controller
{
    public function showLogin(): View
    {
        return view('auth.login');
    }

    public function login(Request $request, LocalApiClient $api): RedirectResponse
    {
        $credentials = $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required'],
        ]);

        $api->login($credentials['email'], $credentials['password']);

        $user = User::query()->firstOrCreate(
            ['email' => $credentials['email']],
            [
                'name' => $credentials['email'],
                'password' => Hash::make($credentials['password']),
                'permissions' => [
                    'platform.index' => true,
                    'platform.autoscale' => true,
                ],
            ]
        );

        $permissions = array_merge(
            ['platform.index' => true, 'platform.autoscale' => true],
            $user->permissions ?? []
        );
        if ($user->permissions !== $permissions) {
            $user->forceFill(['permissions' => $permissions])->save();
        }

        Auth::login($user, $request->boolean('remember'));

        return redirect()->route('platform.main');
    }

    public function logout(LocalApiClient $api): RedirectResponse
    {
        $api->logout();
        Auth::logout();

        return redirect()->route('login');
    }
}
