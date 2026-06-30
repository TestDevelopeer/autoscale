<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class License extends Model
{
    use HasUuids;

    protected $fillable = [
        'organization_id',
        'activation_code',
        'status',
        'modules',
        'limits',
        'expires_at',
        'grace_days',
        'offline_until',
        'machine_fingerprint',
        'status_reason',
        'status_changed_at',
    ];

    protected $casts = [
        'modules' => 'array',
        'limits' => 'array',
        'expires_at' => 'datetime',
        'offline_until' => 'datetime',
        'status_changed_at' => 'datetime',
    ];

    public function organization(): BelongsTo
    {
        return $this->belongsTo(Organization::class);
    }

    public function activations(): HasMany
    {
        return $this->hasMany(LicenseActivation::class);
    }
}
