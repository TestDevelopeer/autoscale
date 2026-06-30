<?php

use App\Http\Controllers\ApiAuthController;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => redirect()->route('login'));

Route::get('/login', [ApiAuthController::class, 'showLogin'])->name('login');
Route::post('/login', [ApiAuthController::class, 'login']);
Route::post('/logout', [ApiAuthController::class, 'logout'])->name('logout');
