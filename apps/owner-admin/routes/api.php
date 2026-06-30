<?php

use App\Http\Controllers\Api\LicenseActivationController;
use App\Models\License;
use Illuminate\Support\Facades\Route;

Route::prefix('api')->group(function () {
    Route::post('licenses/activate', [LicenseActivationController::class, 'activate']);
    Route::post('licenses/offline/issue', [LicenseActivationController::class, 'offlineIssue']);
    Route::post('licenses/{license}/revoke', [LicenseActivationController::class, 'revoke']);
    Route::post('licenses/{license}/suspend', [LicenseActivationController::class, 'suspend']);
    Route::post('licenses/{license}/renew', [LicenseActivationController::class, 'renew']);
});
