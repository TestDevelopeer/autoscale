@php
    use App\Support\AutoscaleLabels;
    $apiStatus = $health['status'] ?? 'unknown';
    $licenseValid = $license['valid'] ?? false;
    $licenseStatus = AutoscaleLabels::licenseStatus($license['status'] ?? null);
@endphp

<div class="row g-3">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">local-api</h5>
                <span class="badge bg-{{ $apiStatus === 'ok' ? 'success' : 'danger' }}">
                    {{ $apiStatus === 'ok' ? 'Работает' : 'Ошибка' }}
                </span>
                <p class="text-muted small mt-2 mb-0">v{{ $health['version'] ?? '—' }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">База данных</h5>
                <span class="badge bg-{{ ($health['database'] ?? '') === 'ok' ? 'success' : 'warning' }}">
                    {{ ($health['database'] ?? '') === 'ok' ? 'Подключена' : ($health['database'] ?? '—') }}
                </span>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Лицензия</h5>
                <span class="badge bg-{{ $licenseValid ? 'success' : 'secondary' }}">{{ $licenseStatus }}</span>
                <p class="small mt-2 mb-0">{{ $license['user_message'] ?? '' }}</p>
            </div>
        </div>
    </div>
</div>
